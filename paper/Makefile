# Rebuild the paper. table.tex is generated from the committed result.json
# artifacts, never hand-edited, so the numbers in the paper and the numbers in
# the repository cannot drift apart.
verification.pdf: verification.tex table.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error verification.tex

table.tex: mktable.py
	python3 mktable.py

clean:
	latexmk -C
	rm -f table.tex
.PHONY: clean
