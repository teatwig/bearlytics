PHONY: dev deploy collectstatic

dev:
	echo "http://localhost:8000"
	python manage.py runserver

deploy:
	git push dokku main

collectstatic:
	python manage.py collectstatic