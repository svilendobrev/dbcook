#$Id$

#PYTHONPATH := $(PYTHONPATH):$(shell pwd)/..
#export PYTHONPATH

test:
	$(MAKE) -C tests/

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

rmpyc:
	rm -f `find . -name \*.pyc `

# vim:ts=4:sw=4:noexpandtab
