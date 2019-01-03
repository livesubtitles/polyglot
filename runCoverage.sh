coverage run --source=server --omit=server/tests/*,server/punctuator2/* --branch -m unittest discover server/tests
coverage report -m
