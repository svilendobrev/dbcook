#$Id$
%.test: %.py
	@echo ===============
	PYTHONPATH=`pwd`/..:$(PYTHONPATH) python $*.py -v $(ARGS)

now: utilz
now: sa
now: mapper

utilz: ../dbcook/kjmincut.test

sa: sa/ref_AxA.test
sa: sa/ref_A_B_A_all.test

mapper: mapper/test4mapper.test
mapper: mapper/test_inh_types.test
mapper: other/walktest1.test
mapper: mapper/mincut.test
mapper: abc
mapper: mapper/relation.test
mapper: other/expression.test
mapper: mapper/freegen/main.test

#abc: ARGS= zno_sisters Binhs=A Cinhs=B Clinks=None doC zdummy
abc: mapper/test_ABC_inh_ref_all.test

AA= doC inhs=j generate=failed,one
abcj: override ARGS+=$(AA)
abcj: abc

#XXX 16 cases failing:
BB = insts=ABC Alinks=C,C1 Binhs= Blinks=A,A1 Cinhs=A Clinks=B,B1
abcj_fail: override ARGS+=$(BB)
abcj_fail: abcj

gen: run_generated_cases.test


################################
#PYTHONPATH := $(PYTHONPATH):$(shell pwd)/..
#export PYTHONPATH


%.t: tests/%.diff
	@:

tests/output/%.result: %.py
	python $*.py -v > $@

proba.dump: proba.db
	echo -e '.dump\n.quit\n' | sqlite3 proba.db

#tests/%.result: %.test
#	@:

.PRECIOUS: %.org tests/output/%.result 	#patterns same as in a rule!
.PHONY: tests/output/%.result 	#patterns same as in a rule!
.PHONY: tests/output/%.diff 	#patterns same as in a rule!
%.org: %.result
	@[ -f $@ ] || ( read -p '$@ original inexisting. create?' -n 1 && [ "$$REPLY" = "y" ] && cp $< $@ && echo '' )
%.diff: %.result %.org
#		may use bash's pipefail-option
	diff -btw $+ > $@ || ( cat $@ && false )
#	diff -btw $+ > $@ && ( rm -f $@ $*.result) || ( cat $@ && rm -f $*.result && false )
#	rm -f $*.result $@
cleantest: clean-test-result
clean-test-%:
	rm -f tests/*.$*

# vim:ts=4:sw=4:noexpandtab
