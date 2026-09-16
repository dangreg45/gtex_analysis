gtex <- read.delim("/Users/dangr/active/06-classes/current/nebula/code/data/gene_reads_adult_gtex_v11_brain_cortex.gct", skip = 2)
dim(gtex)
gtex[1:10, 1:5]
columns <- colnames(gtex)[3:ncol(gtex)]
matrix <- as.matrix(gtex[, columns])
rownames(matrix) <- gtex$Name
col_sum <- colSums(matrix)
summary(col_sum)
hist(col_sum, main = "Reads per sample - Whole Blood", xlab = "Total counts")