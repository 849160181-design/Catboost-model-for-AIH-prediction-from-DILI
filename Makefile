.PHONY: demo test parity r-all data clean

demo:
	python3 quickstart/run_demo.py

test:
	python3 -m unittest discover -s tests -v

parity:
	python3 tests/test_model_parity.py

r-all:
	Rscript run_all.R

data:
	python3 data/generate_synthetic_data.py

clean:
	rm -rf results data/derived __pycache__ tests/__pycache__
	rm -f model/demo_retrained.cbm model/catboost_model.json
