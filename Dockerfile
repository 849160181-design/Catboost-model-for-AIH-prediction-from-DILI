# Minimal reviewer image: no R or CatBoost needed for the five-minute demo.
FROM python:3.11-slim

WORKDIR /repo
COPY . .

# Fail the build if the dependency-free demo or test suite breaks.
RUN python3 -m unittest discover -s tests -v && \
    ./quickstart/run_demo.sh

CMD ["./quickstart/run_demo.sh"]
