"""Run every gene list in results/shinygo/input through ShinyGO and download "Results on all Pathways".

Opens a Firefox window, pastes each list plus the background, switches through the
pathway databases, and saves one CSV per list x database in results/shinygo/output.
Several Firefox windows work at once (n_parallel). Downloads that already exist are skipped, so a re-run only does new lists. Delete an
output file to have it downloaded again.

Setup (once): pip install selenium
Run from the gtex folder: python shinygo_download.py
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

# Settings
input_dir = "results/shinygo/input"
output_dir = "results/shinygo/output"
databases = ["KEGG", "GOBP", "GOCC", "GOMF"]  # names as ShinyGO stores them
url = "https://bioinformatics.sdstate.edu/go/"
timeout = 300  # seconds to wait for ShinyGO before giving up on a step
n_parallel = 3  # Firefox windows working at the same time. 1 = one after another

list_files = sorted(glob.glob(os.path.join(input_dir, "*_up_in_*.txt")) + glob.glob(os.path.join(input_dir, "*_both.txt")))
# Lists from deseq2-interaction.qmd
list_files += sorted(f for f in glob.glob(os.path.join(input_dir, "*_interaction_*.txt")) if not f.endswith("_background.txt"))


def background_for(list_file):
    """Background file from the same comparison and base mean filter as a gene list.
    shinygo_A_vs_B_lfc0-1.5_bm100_up_in_A.txt -> shinygo_A_vs_B_bm100_background.txt"""
    name = os.path.basename(list_file)
    if "_interaction_" in name:  # shinygo_A_vs_B_interaction_age_rising.txt -> shinygo_A_vs_B_interaction_background.txt
        return os.path.join(input_dir, name.split("_interaction_")[0] + "_interaction_background.txt")
    comparison, bm = re.match(r"(.+)_lfc[^_]+_(bm[^_]+)_(?:up_in_|both)", name).groups()
    return os.path.join(input_dir, f"{comparison}_{bm}_background.txt")


def output_for(list_file, db):
    return os.path.join(output_dir, os.path.basename(list_file).replace(".txt", f"_{db}_all.csv"))


# Only keep lists that still have a download missing
todo = {f: [db for db in databases if not os.path.exists(output_for(f, db))] for f in list_files}
todo = {f: dbs for f, dbs in todo.items() if dbs}
for f in todo:
    assert os.path.exists(background_for(f)), "no background file for " + f
print(len(list_files) - len(todo), "lists already done,", len(todo), "to do")
if not todo:
    raise SystemExit

# Parallel: start n_parallel copies of this script, each taking every n-th list, and wait for them.
# A copy is started as "python shinygo_download.py <worker> <n_workers>".
if len(sys.argv) == 3:
    worker, n_workers = int(sys.argv[1]), int(sys.argv[2])
    todo = dict(list(todo.items())[worker - 1::n_workers])
    if not todo:
        raise SystemExit
elif n_parallel > 1 and len(todo) > 1:
    n_workers = min(n_parallel, len(todo))
    workers = [subprocess.Popen([sys.executable, "-u", __file__, str(w), str(n_workers)]) for w in range(1, n_workers + 1)]
    failed = [w.wait() for w in workers]
    print("Done" if not any(failed) else "Some windows stopped early - run again to finish the rest")
    raise SystemExit

# Firefox that saves downloads to a temporary folder without asking
download_dir = tempfile.mkdtemp()
options = webdriver.FirefoxOptions()
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.dir", download_dir)
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/csv,text/plain,application/octet-stream")
driver = webdriver.Firefox(options=options)


def wait_until(condition, what):
    start = time.time()
    while time.time() - start < timeout:
        if condition():
            return
        time.sleep(0.5)
    raise TimeoutError(what)


def wait_idle():
    """Wait until ShinyGO has stopped calculating (not busy for 3 seconds in a row)."""
    time.sleep(1)
    quiet = [0]

    def idle():
        busy = driver.execute_script("return document.documentElement.classList.contains('shiny-busy')")
        quiet[0] = 0 if busy else quiet[0] + 1
        return quiet[0] >= 6

    wait_until(idle, "ShinyGO stayed busy")


def set_text(box_id, text):
    """Fill one of ShinyGO's text boxes and tell Shiny it changed."""
    driver.execute_script(
        """
        const e = document.getElementById(arguments[0]);
        e.value = arguments[1];
        e.dispatchEvent(new Event('input', {bubbles: true}));
        e.dispatchEvent(new Event('change', {bubbles: true}));
        Shiny.setInputValue(arguments[0], arguments[1]);
        """,
        box_id, text)


def shiny_input(name):
    return driver.execute_script("return Shiny.shinyapp.$inputValues[arguments[0]]", name)


# Open ShinyGO (the app sits inside a frame on the page)
driver.get(url)
wait_until(lambda: driver.find_elements(By.ID, "shinyframe"), "ShinyGO page did not load")
driver.switch_to.frame("shinyframe")
wait_until(lambda: driver.find_elements(By.ID, "goButton"), "ShinyGO app did not load")
# The page can appear before Shiny has finished connecting; wait for that too
wait_until(lambda: driver.execute_script("return typeof Shiny !== 'undefined' && typeof Shiny.setInputValue === 'function' && !!Shiny.shinyapp"), "Shiny did not start")
wait_idle()

os.makedirs(output_dir, exist_ok=True)
background_file = None
for list_file, dbs in todo.items():
    name = os.path.basename(list_file).replace(".txt", "")
    genes = open(list_file).read().strip()

    # Load this list's background if it differs from the one already in ShinyGO
    if background_for(list_file) != background_file:
        background_file = background_for(list_file)
        background = open(background_file).read().strip()
        set_text("input_text_b", background)

    set_text("input_text", genes)
    time.sleep(1.5)
    # Click through the page script: a fading download window can block a normal click
    driver.execute_script("document.getElementById('goButton').click()")
    wait_until(lambda: driver.find_elements(By.ID, "selectGO"), "no results appeared")
    wait_idle()

    # Check ShinyGO received both lists in full
    assert len(shiny_input("input_text").split("\n")) == len(genes.split("\n")), "gene list incomplete"
    assert len(shiny_input("input_text_b").split("\n")) == len(background.split("\n")), "background incomplete"
    mapped = driver.execute_script("return (document.body.innerText.match(/[^\\n]*IDs mapped[^\\n]*/) || [''])[0]")
    print(name, "|", mapped)

    for db in dbs:
        driver.execute_script("$('#selectGO')[0].selectize.setValue(arguments[0])", db)
        wait_idle()
        assert shiny_input("selectGO") == db, "database did not switch"

        # "Results on all Pathways" -> Download
        before = set(os.listdir(download_dir))
        driver.execute_script("document.getElementById('askDownloadEnrichmentAll').click()")
        wait_until(lambda: driver.find_elements(By.ID, "downloadEnrichmentAll"), "download window did not open")
        time.sleep(1)
        driver.execute_script("document.getElementById('downloadEnrichmentAll').click()")

        def downloaded():
            new = [f for f in set(os.listdir(download_dir)) - before if not f.endswith(".part")]
            return new[0] if new and os.path.getsize(os.path.join(download_dir, new[0])) > 0 else None

        wait_until(downloaded, "download did not finish")
        out_file = output_for(list_file, db)
        shutil.move(os.path.join(download_dir, downloaded()), out_file)
        print("  saved", out_file)

        # Close the download window if it is still open
        driver.execute_script("const b = [...document.querySelectorAll('.modal button')].find(x => x.innerText.trim() === 'Cancel'); if (b) b.click();")
        time.sleep(1)

driver.quit()
shutil.rmtree(download_dir)
print("Done")
