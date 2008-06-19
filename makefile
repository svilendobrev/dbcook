#$Id$
PY ?= python
#PYTHONPATH := $(PYTHONPATH):$(shell pwd)/..
#export PYTHONPATH

#z: tests/other/aboutrel.test

now: test misc static
test:
	$(MAKE) -C tests/

misc: timed aggr
timed:
	$(MAKE) -C dbcook/misc/timed/db/tests/
aggr:
	$(MAKE) -C dbcook/misc/aggregator/

static: dbcook/usage/static_type/test_autoset_lazy.py
	PYTHONPATH=`pwd`:$(PYTHONPATH) $(PY) $< -v $(ARGS)


ver: _testver rmpyc now
_testver:
	@echo using VER=$(VER)
	test -e "$(VER)" && ln -nfs $(VER) sqlalchemy


%.test: %.py
	@echo ===============
	PYTHONPATH=`pwd` $(PY) $*.py -v $(ARGS)
##############

EXCLUDE1 = \*pyc \*.result \*.ok \*.tmp .svn  \*.tbz \*.bz2 \*.tar  _t\*.py $(EXCLUDE)
_EXCLUDE = $(EXCLUDE1:%=--exclude=%)

NAME = dbcook
TAR = $(NAME)`date +%m%d`.tar
tar:
	svn info |grep 'Last Changed Rev' >version
	rm -rf _tmp
	mkdir -p _tmp/$(NAME)
	cd _tmp/$(NAME); ln -s ../../* .; rm _*
	cd _tmp/$(NAME); ln -sf `python -c 'import util; print util.__path__[0]'` util
	cd _tmp; tar cvjf ../$(TAR).bz2 --dereference $(_EXCLUDE) $(NAME)
	rm -rf _tmp

.PHONY: tag tags
tag tags:
	ctags -R --links=no --exclude=_t\*.py .
	-test -L dbcook && ctags -R -a --exclude=_t\*.py dbcook/
	ctags -R -a sqlalchemy

rmpyc:
	find . -follow -name \*.pyc -exec rm {} \;

# vim:ts=4:sw=4:noexpandtab
