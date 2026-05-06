.PHONY: test capture-demo validate-demo clean

test:
	python -m pytest

capture-demo:
	python -m volcap trigger --config config/node_config.yaml --duration 0.2 --output volcap_data --session-id demo_session

validate-demo:
	python -m volcap validate-session volcap_data/sessions/demo_session

clean:
	rm -rf volcap_data logs .pytest_cache
