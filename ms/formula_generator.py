#encoding:utf-8

from libms.Chemistry.Tools import formulaTable

formulaTable.__doc__ += """

    Examples:

    .. pycon::

       import ms       !onlyoutput
       import mass     !onlyoutput
       m0 = mass.of("C6H12O3")
       mmin, mmax = m0-0.01, m0+0.01
       print mmin, mmax
       tab = ms.formulaTable(mmin, mmax)
       tab.print_()

       # reduce output by putting restrictions on atom counts:
       tab = ms.formulaTable(mmin, mmax, C=6, N=0, P=(0,3), S=0)
       tab.print_()

       # generating all hydrocarbons with a neutral mass below 30:
       tab = ms.formulaTable(1, 30, C=(1, 100), H=(1,100), N=0, O=0, P=0, S=0, prune=False)
       tab.print_()    !shortentable

    """
