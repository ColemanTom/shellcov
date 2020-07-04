
flake8:
	 flake8

bandit:
	 bandit -r ./

pytest:
	pytest -vvv test --cov=shell_cov

