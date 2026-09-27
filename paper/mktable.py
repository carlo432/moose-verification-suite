#!/usr/bin/env python3
"""Emit the paper's results table from the committed case artifacts."""
import math, re, html as H
import casedata

def tex(s):
    s = re.sub(r'<sub>(.*?)</sub>', r'$_{\1}$', s)
    s = re.sub(r'<sup>(.*?)</sup>', r'$^{\1}$', s)
    rep = {'&amp;': r'\&', '&minus;': '$-$', '&nu;': r'$\nu$', '&sigma;': r'$\sigma$',
           '&lambda;': r'$\lambda$', '&theta;': r'$\theta$', '&pi;': r'$\pi$',
           '&sup2;': '$^2$', '&times;': r'$\times$', '&middot;': r'$\cdot$',
           '&ndash;': '--', '&mdash;': '---', '&thinsp;': r'\,', '&#8320;': '$_0$'}
    for k, v in rep.items():
        s = s.replace(k, v)
    return s.replace('$$', '')

def num(v):
    if v == 0:
        return "0"
    e = math.floor(math.log10(abs(v)))
    if -3 <= e <= 1:
        return f"{v:.3g}"
    return f"${v/10**e:.2f}\\times 10^{{{e}}}$"

rows, last = [], None
for cid, item, cls, title, against, metric, err, tol in casedata.load():
    d = item.split('.')[0]
    if d != last:
        strut = r"\rule{0pt}{1.6em}" if rows else r"\rule{0pt}{1.0em}"
        rows.append(rf"\multicolumn{{8}}{{@{{}}l}}{{{strut}\itshape {d}.\ {casedata.DOMAIN[d]}}}\\[1pt]")
        last = d
    p = err / tol * 100
    if p >= 1:      pct = f"{p:.2f}"
    elif p >= 0.01: pct = f"{p:.3f}"
    else:
        ep = math.floor(math.log10(p)); pct = rf"${p/10**ep:.1f}\times 10^{{{ep}}}$"
    mark = r"\,$\dagger$" if err/tol > 0.5 else ""
    rows.append(rf"\texttt{{{cid}}} & {item} & {cls} & {tex(title)} & {tex(metric)} & "
                rf"{num(err)} & {num(tol)} & {pct}{mark}\\")

HEAD = r"""{\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{longtable}{@{}llcp{4.15cm}p{3.25cm}rrr@{}}
\caption{The twenty-five verified capabilities. ``Budget'' is the measured error
as a percentage of the declared tolerance; lower is better. $\dagger$ marks cases
consuming more than half their budget.\label{tab:main}}\\
\toprule
Case & Item & Cl. & Capability & Scored metric & Error & Tol. & Budget \%\\
\midrule
\endfirsthead
\toprule
Case & Item & Cl. & Capability & Scored metric & Error & Tol. & Budget \%\\
\midrule
\endhead
\bottomrule
\endfoot
"""
open('table.tex', 'w').write(HEAD + "\n".join(rows) + "\n\\end{longtable}\n}\n")
print(f"table.tex: {len(casedata.load())} cases")
