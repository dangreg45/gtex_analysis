# GTEx analysis

Whole blood vs. sigmoid colon and whole blood vs. brain cortex differential GTEx analysis.

For most of the analysis files I have tried to design them such that the changes in the settings block will automatically propogate throughout the entire program.

tissue_overlap-analysis.qmd:
- Imports subject and sample annotations
- Analyze by phenotype/covariate for potential sampling bias
- Produce data table outputs paired with tissue expression

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

deseq2-sex_check:
- Imports dds object from analysis
- Runs covariate and interactions effects for sex

brain_stress_hardy:
- Imports raw counts
- Estimates brain stress response in relation to Hardy scale.