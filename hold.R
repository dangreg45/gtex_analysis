# Build one metadata table for just our blood + cortex count columns. The donor ID is the first two dash-separated fields of the sample ID (e.g. `GTEX-1117F-0005-SM-HL9SH` -\> `GTEX-1117F`), used to attach the subject-level phenotypes.

```{r}
# Sample IDs = the count-matrix columns (drop the two gene-annotation columns)
blood.samples  <- setdiff(colnames(blood.dt),  c("Name", "Description"))
cortex.samples <- setdiff(colnames(cortex.dt), c("Name", "Description"))

# Per-sample attributes, indexed by sample ID (Broad-style bracket indexing)
meta <- sample.df[c(blood.samples, cortex.samples), c("SMTSD", "SMRIN", "SMTSISCH")]
meta$tissue <- c(rep("blood",  length(blood.samples)),
                 rep("cortex", length(cortex.samples)))

# Donor ID -> attach subject-level phenotypes
meta$SUBJID  <- sub("^(GTEX-[^-]+).*", "\\1", rownames(meta))
meta$SEX     <- factor(subject.df[meta$SUBJID, "SEX"], levels = c(1, 2),
                       labels = c("male", "female"))
meta$AGE     <- subject.df[meta$SUBJID, "AGE"]
meta$DTHHRDY <- subject.df[meta$SUBJID, "DTHHRDY"]

head(meta)
```

# Cohort comparison (selection-bias check)

The two tissues come from different, non-random donor subsets (e.g. GTEx did not collect brain from donors ventilated \>=24h before death), so their donors differ systematically. Comparing demographics and technical covariates makes that skew visible -- large imbalances here are confounders to model, not just nuisance.

```{r}
# Donor characteristics by tissue
table(meta$tissue, meta$SEX)
table(meta$tissue, meta$DTHHRDY)              # Hardy death-classification scale (0-4)
addmargins(table(meta$tissue, meta$AGE))

# Technical covariates (tissue means)
aggregate(cbind(SMRIN, SMTSISCH) ~ tissue, data = meta,
          FUN = function(x) round(mean(x, na.rm = TRUE), 1))
```










## Representativeness tests

Attempt statistical tests to support/disprove bias concerns.

Potentially helpful source: <https://atm.amegroups.org/article/view/22865/html>
  
  ```{r}
# Test whether two donor groups (a, b) have the same distribution of one covariate.
rep_test <- function(a, b, var) {
  x <- subject.dt[SUBJID %in% a][[var]]   # covariate values for group a
  y <- subject.dt[SUBJID %in% b][[var]]   # covariate values for group b
  # Build a contingency table: covariate level (rows) x group A/B (columns).
  tab <- table(factor(c(x, y)),
               rep(c("A", "B"), c(length(x), length(y))))
  # Fisher's exact test; Monte Carlo (B draws) because tables can be large/sparse.
  suppressWarnings(
    fisher.test(tab, simulate.p.value = TRUE, B = 20000)$p.value)
}

# Run the test for each covariate and collect one row of p-values per covariate.
rep.results <- rbindlist(lapply(c("SEX", "AGE", "DTHHRDY"), function(v)
  data.table(
    covariate            = v,
    # overlap vs cortex-only: is the paired subset like the rest of cortex?
    p_overlap_vs_cortexOnly = round(rep_test(overlap.donors, cortex.only.donors, v), 4),
    # overlap vs blood-only: is the paired subset like the rest of blood?
    p_overlap_vs_bloodOnly  = round(rep_test(overlap.donors, blood.only.donors,  v), 4)
  )))
rep.results
```