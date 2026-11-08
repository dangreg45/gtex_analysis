# GTEx analysis

Whole blood vs. sigmoid colon and whole blood vs. brain cortex differential GTEx analysis.

For most of the analysis files I have tried to design them such that the changes in the settings block will automatically propogate throughout the entire program.

brain_stress_hardy:
- Imports raw counts
- Estimates brain stress response in relation to Hardy scale.

deseq2-analysis.qmd:
- Imports overlap output
- Initial object anaylsis
- Filter out low gene counts
- Fit model
- Investigate shrinkage effects
- Output

deseq2-figures:
- Imports analysis output
- Builds supplementary figures to the analysis

deseq2-gene_lists:
- Imports analysis output
- Keeps hits within a band of fold changes
- Writes gene lists for ShinyGO

deseq2-sex_check:
- Imports dds object from analysis
- Runs covariate and interactions effects for sex

shinygo_download.py:
- Created this with Claude. I've verified the results are consistent with manual trials.
- Automated pipeline to run staged DESEq results through ShinyGO using GOBP, GOMF, GOCC, and Kegg

shinygo-compare.qmd:
- Visualize fold enrichment between phenotype groups
- Plots pathways found in one group but not the other - helpful for IDing potentially problematic sample size differences

shinygo-figures.qmd:
- Creates lollipop plots similar to those produced in the ShinyGO website
- Uses reference datasets to ID some pathways

tissue_overlap-analysis.qmd:
- Imports subject and sample annotations
- Analyze by phenotype/covariate for potential sampling bias
- Produce data table outputs paired with tissue expression

# PTSD Analysis

This analysis uses PTSD RNAseq data to identify candidate blood test markers for predicting stress information. Note that deseq2-analysis.qmd from above is used for the differential expression stage.

hpa_secreted.qmd:
- Uses Human Protein Atlas v25.1 to identify which genes are secreted to the blood.

ptsd_input:
- Reads in NCBI dataset for the 2017 Kuan PTSD study. Uses the following files:
  - Raw counts
  - Gene annotation
  - Sample matrix
  
blood_markers.qmd:
- Filters DESeq results to only include the secreted to blood genes
- Performs other misc. checks that do not directly affect the pipeline.

markers_auc.qmd:
- Calculates AUC for all of the differentially expressed candidate markers.