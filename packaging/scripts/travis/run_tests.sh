# have to do `which trial` instead of simply trial because coverage needs the full path
coverage run --source=lbrynet `which trial` tests
coveralls