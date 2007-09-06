#$Id$
# -*- coding: cp1251 -*-

'''
възможности за добавяне/помнене на състояние 'изтрит/изключен':
 1: отделна история на Състоянието:
    - помненето не е заедно с Обекта - може да е проблем (БД/таблици)
    - не може да се изнесе Състоянието навън през Обекта - не знае нищо за него
 2: помни се огъвка на Обекта със Състояние, напр. наредена двойка:
    - не се пипа Обекта
    - не може да се изнесе Състоянието навън през Обекта
 3: слага/променя се атрибут Състояние/disabled на Обекта, и се помни така променения Обект:
    - може да се изнесе Състоянието навън - Обектът си го носи
    - Обектът се пипа, т.е. трябва му се прави _копие_ + новото състояние
 4: помни се огъвка, която има Състояние, и за всичко друго препраща към Обекта:
    - не всичко ще работи 100%, напр. isinstance, issubclass трябва да се
        подменят да виждат Обекта, а не огъвката

 == дотук се предполага, че изтритият Обект трябва да си пази стойността
    (напр. последната валидна преди изтриването)
 5: изтриването не се помни като Обект изобщо, а _вместо_ Обект се помни някакъв Символ,
        означаващ "изтрито състояние"
    - ако е нужна стойността ПРЕДИ изтриването, тя ще трябва да се търси допълнително,
        и резултатът може да не е същия като В МОМЕНТА на изтриването - въпрос на търсене/ключ -
        и ще изисква поддръжка от долното Timed* ниво!

Всъщност тук има 2 различни смисъла на "стойността на изтрития обект":
eдиният е _точната_ стойност в момента на изтриване (2,3,4 дават това),
другият е "дай последна валидна стойност" (5, и кое-да-е с оптимизация на изтриването).

 6: при условие, че е нужно да се помни ТОЧНАТА стойност в момента на изтриване,
трябва да се направи комбинация от 1 и някоя огъвка: Обектите се помнят както са си,
и има отделна история на Състоянието, която помни състояние+връзка към Обект от историята.

възможности за съобщаване/изнасяне на състоянието при необходимост:
 а: връща символи: (няма обект - или обект, или състояние)
    return Липсва / Изтрит (частен случай None/None - без разлика в причината)
 б: Изключения: (няма обект - или обект, или състояние)
    raise Липсва / Изтрит
 в: слагане на атрибут в Обекта (не винаги е възможно ???)
    obj.disabled = Липсва / Изтрит; return obj
 г: връща се огъвка, която има Състояние, и за всичко друго препраща към Обекта:
    return WrapProxy( obj, disabled= Липсва/Изтрит)
    - не всичко ще работи 100% (също като 4 по-горе)

------- друго -----
 - оптимизация от типа 'не слагай _изтрит_ ако е вече изтрит' може да не е еквивалентна:
    напр. при наличие на изтрит(1.11); пуска се изтрит(5.11); после се пуска неизтрит( 3.11)
    резултатът към 5.11 с и без оптимизация ще е различен - има/няма обект.
    Разбира се, това не значи че трябва да се разреши/прави изтриване на изтрит обект - просто
    решението за това трябва да се вземе на доста по-високо ниво.
 - 3) и в) не стават освен ако ВСИЧКИ обекти си имат .disabled по принцип;
    освен това копирането може да е доста бавна операция;
 - 5) изглежда най-елегантно - като изключим търсенето... А НУЖНО ЛИ Е ТО?

Та, кое да бъде?

'''

#помнене
_USE_WRAPPER_TUPLE = 0              #2
_USE_OBJECT_ATTR = 0                #3
class DisabledState: pass
_USE_SYMBOL_INSTEAD_OF_OBJECT = 1   #5
_USE_SEPARATE_HISTORY6 = 0          #6

#съобщаване/изнасяне
#? сега е а)

class Disabled4Timed( object):
    __slots__ = ()
    DisabledKlas = DisabledState
    #NOT_FOUND = ... from timed

    # очаква _get_val() / _put_val() за достъп до Timed* основа
    def _get( me, time, include_disabled =False, **kargs):
        value = me._get_val( time, **kargs)
        if value is me.NOT_FOUND:
            #print 'empty', value
            return value                # няма записи все-още

        try:
            if _USE_WRAPPER_TUPLE:
                value,disabled = value      #value НЯМА да знае дали е disabled !
            elif _USE_OBJECT_ATTR:
                disabled = value.disabled   #value си носи disabled
            elif _USE_SYMBOL_INSTEAD_OF_OBJECT:
                disabled = value is me.DisabledKlas
            else: raise NotImplementedError
        except (AttributeError, ValueError):
            disabled = False

        if disabled and not include_disabled:
            #print 'disabled', value
            return me.NOT_FOUND         # 'изтрит' - raise

        #if _USE_SYMBOL_INSTEAD_OF_OBJECT:
            #XXX намери последната валидна стойност ПРЕДИ изтриването.. НУЖНО ли е това?
            #XXX няма да се намери _точно_ стойността по време на изтриването!
            #XXX ще изисква поддръжка от долното Timed* ниво!
        return value

    def _getRange( me, timeFrom, timeTo, include_disabled =False, **kargs): #not quite clear, but works
        return me._get_range_val( timeFrom, timeTo, **kargs)
    def _put( me, value, time, disabled =False):
        if _USE_WRAPPER_TUPLE:
            value = value,disabled
        elif _USE_OBJECT_ATTR:
            value.disabled = disabled
            #XXX тук трябва да се прави копие!
            #except AttributeError: #cannot be disabled
        elif _USE_SYMBOL_INSTEAD_OF_OBJECT:
            if disabled:
                value = me.DisabledKlas
        else: raise NotImplementedError
        me._put_val( value, time)

    def delete( me, time):
        #XXX няма оптимизация за изтриване на вече изтрит;
        # ако е нужна(???), сложи me._get(..) вместо пряко me._get_val()
        value = me._get_val( time)
        if value:
            me._put( value, time, disabled=True)

if _USE_SEPARATE_HISTORY6:
    class Disabled4Timed6( object):
        def __init__( me, TimedKlas):
            me.state = TimedKlas()
        #... всичко е друго!

# vim:ts=4:sw=4:expandtab:enc=cp1251:fenc=
