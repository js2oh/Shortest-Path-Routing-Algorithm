script:
	@echo "python router.py 1 ubuntu1604-006 13000 13001 &" >router 2>&1;
	@echo "python router.py 2 ubuntu1604-006 13000 13002 &" >>router 2>&1;
	@echo "python router.py 3 ubuntu1604-006 13000 13003 &" >>router 2>&1;
	@echo "python router.py 4 ubuntu1604-006 13000 13004 &" >>router 2>&1;
	@echo "python router.py 5 ubuntu1604-006 13000 13005"   >>router 2>&1;
	chmod a+x router
	