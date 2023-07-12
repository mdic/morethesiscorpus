# WORK IN PROGRESS!

# MoReThesisCorpus: Documenting Academic Language as Used in the Theses Submitted to the University of Modena and Reggio Emilia

## Description

This repository contains the scripts described in Bondi and Di Cristofaro (2023), and employed to compile the MoreThesisCorpus  
  
A brief description - adapted from Bondi and Di Cristofaro 2023:17 - of each script is provided below, where each script is labelled with `S` followed by a progressive two-digit number.

`S01`: acquisition of the HTML catalogue cards (i.e.,the web pages hosted on the MoReThesis platform)  
`S02`: extraction of the metadata points from the HTML tables, which are then saved to a spreadsheet  
`S03`: acquisition of the PDF files (when publicly available)  
`S04`: extraction of the text and additional markup from the PDF files  
`S05`: creation of the final XML corpus files by merging the extracted text and the extracted metadata (collected with script `S02`)  

## How to cite
If using the script(s), please cite the following

```bib

@article{bondi_morethesiscorpus_2023,
	title = {{MoReThesisCorpus}: {Documenting} {Academic} {Language} as {Used} in the {Theses} {Submitted} to the {University} of {Modena} and {Reggio} {Emilia}},
	copyright = {Copyright (c) 2023 Marina Bondi, Matteo Di Cristofaro},
	issn = {2281-4582},
	shorttitle = {{MoReThesisCorpus}},
	url = {https://iperstoria.it/article/view/1265},
	doi = {10.13136/2281-4582/2023.i21.1265},
	language = {en},
	number = {21},
	urldate = {2023-07-12},
	journal = {Iperstoria},
	author = {Bondi, Marina and Cristofaro, Matteo Di},
	month = jun,
	year = {2023},
	note = {Number: 21},
	keywords = {academic discourse, academic writing, corpus linguistics, eap},
	pages = {9--30},
}

```