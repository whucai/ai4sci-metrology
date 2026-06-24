The disruption index is biased by citation inflation
Alexander Michael Petersena,,1 Felber Arroyave,1 and Fabio Pammolli2
1Department of Management of Complex Systems, Ernest and Julio Gallo Management Program,
School of Engineering, University of California, Merced, California 95343, USA
2Politecnico Milano, Department of Management, Economics and Industrial Engineering, Via Lambruschini, 4/B, 20156, Milan, Italy
A recent analysis of scientific publication and patent citation networks by Park et al. (Nature, 2023) suggests that publi-
cations and patents are becoming less disruptive over time. Here we show that the reported decrease in disruptiveness
is an artifact of systematic shifts in the structure of citation networks unrelated to innovation system capacity. Instead,
the decline is attributable to ‘citation inflation’, an unavoidable characteristic of real citation networks that manifests
as a systematic time-dependent bias and renders cross-temporal analysis challenging. One driver of citation inflation is
the ever-increasing lengths of reference lists over time, which in turn increases the density of links in citation networks,
and causes the disruption index to converge to 0. A second driver is attributable to shifts in the construction of reference
lists, which is increasingly impacted by self-citations that increase in the rate of triadic closure in citation networks,
and thus confounds efforts to measure disruption, which is itself a measure of triadic closure. Combined, these two
systematic shifts render the disruption index temporally biased, and unsuitable for cross-temporal analysis. The impact
of this systematic bias further stymies efforts to correlate disruption to other measures that are also time-dependent,
such as team size and citation counts. In order to demonstrate this fundamental measurement problem, we present
three complementary lines of critique (deductive, empirical and computational modeling), and also make available an
ensemble of synthetic citation networks that can be used to test alternative citation-based indices for systematic bias.
A measure of disruption was recently developed and applied to empirical citation networks [1–3]. This bibliometric measure,
denoted by CD, quantifies the degree to which an intellectual contribution p (e.g. an research publication or invention patent)
supersedes the sources cited in its reference list, denoted by the set {r}p. As defined, CDp is measured according to the local
structure of the subgraph Gp = {r}p ∪p ∪{c}p comprised of the focal node p, nodes belonging to its reference list {r}p, and
the set of nodes citing either p or any member of {r}p, denoted by {c}p. If future intellectual contributions cite p but do not cite
members of {r}p, then it is argued that p plays a disruptive role in the citation network. However, the critical issue we highlight
is the following: as the length rp = |{r}p| of the reference list increases, so does the likelihood that one of those papers is
highly cited. Hence, CDp is a biased measure because reference lists have increased dramatically over time, and so too have the
number of citations that highly-cited papers accrue [4] – both phenomena being bi-products of citation inflation [5].
Citation inflation (CI) refers to the systematic increase in the number of links introduced to the scientific (or patent) citation
network each year. CI is analog to monetary inflation [6, 7], whereby as a government prints more money the sticker price
of items tends to go up, rendering the impression that the real cost of goods are increasing (to what degree this relationship
is valid depends on wage growth and a number of other economic factors). By analogy, it might also be tempting to attribute
the increased volume of scientific production to techno-social productivity increases, yet this explanation neglects the persistent
growth rate of the inputs (e.g. researchers and research investment) that are fundamental to the downstream production of outputs
(e.g. research articles, patents.
Indeed, secular growth underlies various quantities relevant to the study of the scientific endeavor, from national expenditures
in R&D to the population size of researchers [5] and the characteristic number of authors per research publication [8–10] –
all quantities that have persistently grown over the last century. Nevertheless, the degree to which such growth affects the
quantitative evaluation of research outcomes is under-appreciated, and can manifest in inconsistent measurement frameworks
and metrics. Indeed, the number of citations an article receives is not solely attributable to novelty or prominence of the research,
but also depends on the the population size and citing norms of a discipline, and quite fundamentally, the nominal production
rate of links in the citation network, among other considerations [11]. Hence, there is real need to distinguish nominal counts
versus real values in scientific evaluation, which in the analysis of citation networks requires accounting for when each citation
was produced, and in further extensions, how the credit is shared [5, 10, 12, 13].
So what are the main sources of CI in scientific citation networks and what are the real-world magnitudes of their effects?
Figure 1(a) illustrates how CI arises through the combination of longer reference lists, denoted by r(t), compounded by an
increasing production volume, n(t). By way of real-world example, prior calculation of the growth rate of total number of
citations produced per year based upon the entire Clarivate Analytics Web of Science citation network estimated that the total
volume C(t) ≈n(t)r(t) of citations generated by the scientific literature grows exponentially with annual rate gC = gn + gr =
0.033 + 0.018 = 0.051 [4]. Hence, with the number of links in the citation network growing by roughly 5% annually, the total
number of links in the citation doubles every ln(2)/gC = 13.6 years!
[a] Send correspondence to: apetersen3@ucmerced.edu
arXiv:2306.01949v1  [cs.DL]  2 Jun 2023
2
While the dominant contributor to CI is the growth of n(t) deriving from increased researchers and investment in science
coupled with technological advances increasing the rate of manuscript production, the shift away from print towards online-only
journals, and the advent of multidisciplinary megajournals [14], the contribution to CI from growing reference lists alone is
nevertheless substantial and varies by discipline [15–18]. By way of example, consider descriptive statistics based upon analysis
of millions of research publications comprising the Microsoft Academic Graph (MAG) citation network [19]: in the 1960s, the
average (± standard deviation) number of references per articles was rp = 9 (±17); by the 2000s, rp increased to 23 (±27),
a 2.6-fold increase over the 50-year period – see Fig. 1(b). Meanwhile, as research team sizes – denoted by kp, and used as
a proxy for the production effort associated with a research output – increase in order to address research problems featuring
greater topical and methodological breadth, there emerges a non-linear relationship between rp and kp showing that the modern
research article is fundamentally different from those produced even a decade ago – see Fig. 1(c). Thus, not only does the
nominal value of a citation vary widely by era, but the implications of secular growth on the topology of the citation network and
thus citation-based research evaluation are profound [4]. A standard solution to taming variables that are susceptible to inflation
is to use a deflator index, which amounts to normalizing the cross-temporal variation by way of standardized reference point
[5, 12]. Another more nefarious problem is the accurate measurement of the quantitative relationship between variables that are
independently growing over time, which is susceptible to omitted variable bias if the role of time is neglected.
In what follows, we demonstrate the implications of CI that render CD unsuitable for cross-temporal analysis, and call into
question the empirical analysis and interpretations of trends in scientific and technological advancement based upon CD [2, 3].
To establish how the disruption index suffers from citation inflation and is confounded by shifts in scholarly citation practice,
we employ three different approaches: deductive analysis based upon the definition of CDp, empirical analysis of the Microsoft
Academic Graph (MAG) citation network, and computational modeling of synthetic citation networks. In the latter approach, we
are able to fully control the sources of the systematic bias underlying CD (namely CI), thereby demonstrating that CD follows
a stable frequency distribution in the absence of CI. We conclude with research evaluation policy implications.
1.
Quantitative definition of CD and a deductive critique
The disruption index is a higher-order network metric that incorporates information extending beyond the first-order links
connecting to p – those nodes that cite p and are prospective (forward looking or diachronous), and those nodes that are referenced
by p, and thus retrospective (backward looking or synchronous) [20, 21]. The original definition of CD was formulated as a
conditional sum across the adjacency matrix [1], and was subsequently reformulated as a ratio [2]. According to the latter
conceptualization, calculating CDp involves first identifying three non-overlapping subsets of citing nodes, {c}p = {c}i ∪
{c}j ∪{c}k, of sizes Ni, Nj and Nk, respectively – see Fig. 2(a) for a schematic illustration.
The subset i refers to members of {c}p that cite the focal p but do not cite any elements of {r}p, and thus measures the degree
to which p disrupts the flow of attribution to foundational members of {r}p. The subset j refers to members of {c}p that cite
both p and {r}p, measuring the degree of consolidation that manifests as triadic closure in the subnetwork (i.e., network triangles
formed between p, {r}p, {c}j). The subset k refers to members of {c}p that cite {r}p but do not cite p. As such, the CD index
is given by the ratio,
CDp =
Ni −Nj
Ni + Nj + Nk
,
(1)
which can be rearranged as follows,
CDp = (Ni −Nj)/(Ni + Nj)
1 + Nk/(Ni + Nj)
= CDnok
p
1 + Rk
.
(2)
The ratio Rk = Nk/(Ni + Nj) ∈[0, ∞) is an extensive quantity that measures the rate of extraneous citation, whereas
CDnok
p
∈[−1, 1] is an intensive quantity. The polarization measure CDnok
p
is an alternative definition of disruption that simply
neglects Nk in the denominator [22]; for this reason, characteristic values of CDnok
p (t) are larger and decay more slowly over
time then respective CDp(t) values – see ref. [3]. Following initial criticism regarding the definition of CDp [22, 23], other
variations on the theme of CD have since been analyzed [2] and critiqued according to their advantages and disadvantages [24].
To summarize, we argue that a simple deductive explanation trumps the alternative socio-technical explanations offered [3, 25]
for the decline in CD calculated for publications and patents. Namely, the disruption index CDp systematically declines, along
with similar CDp variants [2, 22, 24], for the simple reason that CD features a numerator that is bounded and a denominator
that is unbounded. More technically, the term Rk is susceptible to CI, which is entirely sufficient to explain why CD converges
to 0 over time.
3
b
Number of coauthors, kp
Distribution of # references 
per article, ￼Py(rp)
MAG : 1960-2010
1960s
1970s
1980s
1990s
2000s
1
5
10
50
100
500 1000
10-10
10-7
10-4
0.1
1
2
3
4
5
6
7
8
9
10
0
5
10
15
20
25
Ave. # references per article, ￼rk
Number of references, rp
Inﬂation of the 
reference supply, r(t)
1970
2020
r(t)
n(t)
Inflation of the reference supply
due to growth of r(t) and n(t)
a
2000s
1980s
1960s
c
FIG. 1: ‘Citation inflation’ attributable to the increasing num-
ber and length of reference lists. (a) Schematic illustrating the
inflation of the reference supply owing to the fact that the annual
publication rate n(t) (comprised of increasing diversity of arti-
cle lengths), along with the number of references per publication
r(t), have grown exponentially over time t, which implies a non-
stationary cross-generational flow of attribution in real citation net-
works. Such citation inflation cannot be controlled by way of fixed
citation windows [5]. (b) The probability density function Py(rp)
of the number of references per article rp calculated for articles
included in the MAG citation network grouped by the decade of
publication y. Vertical dashed lines indicate the average value; ver-
tical solid lines indicate the 90th percentile, such that only the 10%
largest rp values are in excess of this value. (c) Conditional rela-
tionship between two quantities that systematically grow over time
(kp and rp). Note the increasing levels and slope of the relationship
over the 50-year period. This relationship indicates that regressing
CDp on kp – while omitting rp as a covariate and thereby neglect-
ing the negative relationship between CDp and rp – may lead to
the confounded conclusion that CDp decreases as kp increases.
2.
Empirical critique
In this section we show empirically that CDp declines over time due to the runaway growth of Rk(t), and implicitly, r(t).
While our results are based upon a single representation of the scientific citation network made openly available by the MAG
project [19], the implications are generalizable to citation networks featuring CI characterized by a non-stationary number of
new links introduced by each new cohort of new citing items. To be specific, the citation network we analyzed is formed from
the roughly 29.5 × 106 million research articles in the MAG dataset that have a digital object identifier (DOI), were published
between 1945-2012, and belonging to a mixture of research areas.
Figure 2(a) shows a schematic of the sub-graph used to calculate the CDp value for each publication. To be consistent with
[2, 3], we calculate CDp,CW (t) using a CW = 5-year citation window (CW), meaning that only articles published within 5
years of p are included in the subgraph {c}p = {c}i ∪{c}j ∪{c}k. As such, Fig. 2(b) shows a decline in the average CD5(t)
that is consistent with the overall trend shown in Fig. 2 in ref. [3], where the data are disaggregated by discipline; also note that
Fig. 2 and ED Figs. 6 and 9 in [3] show that disciplines with higher publication volumes and thus more references produced
(life sciences and biomedicine, and physical sciences) tend to have smaller CD5(t) values in any given year relative to the social
sciences (e.g. JSTOR), which is qualitatively consistent with our critique.
We also note that while the implementation of a CW may control for right-censoring bias, it does not control CI in any
precise way. By way of example, consider the impact of the CW on Nk, the number of extraneous articles that do not cite p
but do cite elements of {r}p. A CW will reduce the number of papers contributing to CD5(t) via Nk, but it will also reduce
Ni + Nj in similar proportions, leaving the ratio Rk(t) unchanged, on average. Consider a more quantitative explanation that
starts by positing that Nk increases proportional to n(t)r(t), as the nodes belonging to {c}k are unconstrained by the first-order
4
Ni + Nj + Nk
 Ni — Nj
CDp = 
=  (10-1)/(10+1+2) = 0.69
Year, t
Average ￼
 
r(t)
A
CDt = const. + βkLog[#Authors] + βrLog[#Refs]
+βcL og[#Cites] + Dt + ϵt
Output of linear regression implemented in STATA 13.0 using xtreg
1950
1960
1970
1980
1990
2000
2010
0
30
60
90
120
150
180
Average  ￼Rk(t)
Results for MAG dataset 
[1945-2012, N = 30 million articles]
￼R2 = 0.96
[w/ Year fixed effects]
Marginal effect on ￼
 
[All covariates held at constant at mean value]
CD5(t)
a
Marginal effect on ￼
 
[All covariates held at constant at mean value]
C D5(t )
￼+0.0039 ± 0.0008
￼−0.025 ± 0.001
On average, a paper with twice as many 
references (2r) has a CD that is -.023*Log[2] = 
-0.017 smaller than if it had r references
On average, a paper with 5 times as many 
coauthors (5K) has a CD that is 0.0039*Log[5] = 
0.006 larger than if it had K coauthors
1.5
2.0
2.5
3.0
3.5
4.0
-0.08
-0.06
-0.04
0.0
0.5
1.0
1.5
2.0
2.5
-0.075
-0.070
-0.065
Ln (# References)
Ln (# Authors)
Model specification:
b
d
f
STATA regression
e
g
publication p
{c}i
{c}j
{c}k
{r}p         
Ni + Nj + Nk
 Ni — Nj
CDp = 
=  (10-1)/(10+1+2) = 9/13 = 0.69
Rk,p = Nk  / (Ni + Nj) = 2 / 11 = 0.182
Ave. ￼r(t)
Ave.  ￼Rk(t)
10
15
20
0
10
20
30
40
50
60
1960
1980
2000
0
10
20
Average ￼
 
CD5(t)
c
1960
1980
2000
0.00
0.04
0.08
FIG. 2: Empirical analysis of the disruption index. (a) Schematic of the disruption index calculation based upon the sub-network revolving
around the source publication/patent p. The disruption index CDp can be calculated by identifying three non-overlapping subsets of {c}p =
{c}i ∪{c}j ∪{c}k, of sizes Ni, Nj and Nk, respectively. The subset i refers to members of {c}p that cite the focal p but do not cite any
elements of {r}p, and thus measures the degree to which p disrupts the flow of attribution to foundational members of {r}p. The subset j
refers to members of {c}p that cite both p and {r}p, measuring the degree of consolidation that manifests as triadic closure in the subnetwork
(i.e., network triangles formed between p, {r}p, {c}j). The subset k refers to members of {c}p that cite {r}p but do not cite p. (b) Average
disruption index, CD5(t) calculated using a 5-year citation window based upon 29.5×106 articles from the MAG dataset from 1945-2012. (c)
Average number of references per paper per year, r(t), which increased by a factor of 4 over the 6-year period shown. (d) Average extraneous
citation rate, Rk(t) ≫1 that is central to the critique of CD, and derives from the increasing citation count of highly-cited papers belonging
to the reference list {r}p which systematically inflates the size of the extraneous set {c}k. (inset) Rk(t) grows roughly proportional to r(t).
(e) Results of linear regression model implemented in STATA 13 for dependent variable CDp,5, controlling for rp and secular growth by way
of yearly fixed-effects. Publication years are within the 20-year range 1990-2009; covariates are included following a logarithmic transform.
(d) Marginal effects calculated with all other covariates held at their mean values, showing that CD5 is negatively correlated with the log of
the number of references, ln rp. (e) CD5 is positively correlated with the log of the number of coauthors, ln kp.
citation network {c}i ∪{c}j ∪{r}p. Following the same logic, Ni + Nj grows proportional to n(t). In both cases, even if the
proportionality constant depends weakly on CW, the ratio Rk(t) will grow proportional to r(t).
There is likely to be considerable variance in the publication-level relationship between Rk,p and rp, because if any member
of {r}p is highly cited, then Nk is skewed towards the heavy right tail of the citation distribution. Moreover, the base number
of citations associated with extreme values in the citation distribution have increased dramatically over the last half century as
a result of CI, such that the number of citations C(Q|t) corresponding to the Q =99th percentile of the citation distribution
increased at an annual rate of roughly 2% from roughly 55 citations in 1965 to roughly 125 citations in 2005 – see Fig. 4 in ref.
[4]. For this reason, the term Nk introduces susceptibility to CI according to two channels.
Here we focus on the channel associated with the growth of r(t), which grew at roughly the same rate as C(99|t), growing
from roughly 9 to 23 references per paper over the same period – see Fig. 2(c). Consequently, Rk(t) ≫1 for nearly the entire
period of analysis and that the growth of Rk(t) is largely explained by the growth of r(t) in the empirical data – see Fig. 2(d).
For this reason, it is more accurate to describe CD as converging to 0 as opposed to decreasing over time.
5
In order to confirm these aggregate-level relationships at the publication level, we applied a linear regression model whereby
the unit of analysis is an individual publication. The linear model specification is given by
CDp,5 = b0 + bk ln kp + br ln rp + bc ln cp + Dt + ϵt
(3)
which controls for secular growth by way of yearly fixed-effects, denoted by Dt. The results of the ordinary least squares
(OLS) estimation using the STATA 13.0 package xtreg are shown in Fig. 2(e), and are based upon 3 million publications with
1 ≤kp ≤10 coauthors, 5 ≤rp ≤50 references, and 10 ≤cp ≤1000 citations that were published in the two-decade
period 1990-2009. The independent variables are modeled using a logarithmic transform because they are each right-skewed:
“LogK” corresponds to ln kp; “LogNRefs” corresponds to ln rp; and LogNCites corresponds to ln cp = ln(ci + cj), the number
of citations received by p in the 5-year window. This sample of MAG articles were used so that results are more closely
comparable to Wu et al. who focus on articles with kp ∈[1, 10] [2].
Results indicate a negative relationship between CDp,5 and the number of references, consistent with our deductive argument.
Figure 2(f) shows the marginal relationship with ln rp, holding all covariates at their mean values, and indicates a net shift in
CD of roughly -0.06 units as rp increases by a factor of 10 from 5 to 50 total references. Similarly, Fig. 2(g) shows the
marginal relationship with ln kp, indicating a net shift in CD of roughly +0.01 units as kp increases by a factor of 10 from 1 to
10 coauthors, which is in stark contrast to the relationship with opposite sign reported in ref. [2].
3.
Computational critique
3.1.
Generative network model featuring citation inflation and redirection
We employ computational modeling to explicitly control several fundamental sources of variation, and to also explore com-
plementary mechanisms contributing to shifts in CD over time – namely, shifts in scholarly citation practice. Our identification
strategy is to growth synthetic citation networks that are identical in growth trajectory and size, but differ just in the specification
of (i) r(t) and/or (ii) the rate of triadic closure denoted by β that controls the consolidation-disruption difference defining the
numerator of CD.
We model the growth of a citation network using a model originally developed in ref. [4] that applies Monte Carlo (MC)
simulation to operationalize stochastic link dynamics by way of a random number generator. This model belongs to the class of
growth and redirection models [26, 27], and reproduces a number of statistical regularities established for real citation networks
– both structural (e.g. a log-normal citation distribution [28]) and dynamical (e.g., increasing reference age with time [4];
exponential citation life-cycle decay [29]). – see the Appendix Section A1 and Fig. A1 for more information regarding the
empirical validation of our generative network model. The synthetic networks constructed and analyzed in what follows are
openly available [30] and can be used to test CD and other citation-network based bibliometric measures for sensitivity to CI
and other aspects of secular growth.
We construct each synthetic citation network by sequentially adding new layers of nodes of prescribed volume n(t) in each
MC period t ≥0 representing a publication year. Each new node, denoted by the index a, represents a publication that could
in principal cite any of the other existing nodes in the network. As such, the resulting synthetic networks are representative of
a single scientific community, and also lack latent node-level variables identifying disciplines, authors, journals, topical breadth
or depth, etc.
We seed the network with n(t = 0) ≡30 ‘primordial’ nodes that are disconnected, i.e. they have reference lists of size
ra ≡0. This ensures that the initial conditions are the same for all networks generated. All nodes added thereafter have
reference lists of a common prescribed size, denoted by r(t). These rules ensure there is no variation within a given publication
cohort regarding their synchronous connectivity. To model the exponential growth of scientific production, we prescribe the
number of new “publications” according to the exponential trend n(t) = n(0) exp[gnt]. We use gn ≡0.033 as the publication
growth rate empirically derived in prior work [4]. Similarly, we prescribe the number r(t) of synchronous (outgoing) links
per new publication according to a second exponential trend r(t) = r(0) exp[grt]. For both n(t) and r(t) we use their integer
part, and plot their growth in Fig. 3(a). We set the initial condition r(0) ≡25 in scenarios featuring no reference list growth
(characterized by gr = 0), such that each new publication cites 25 prior articles independent of t. Alternatively, in scenarios
that do feature reference list CI, we use the empirical growth rate value, gr ≡0.018 and r(0) ≡5. We then sequentially add
cohorts of n(t) publications to the network over t = 1...T ≡150 periods according to the following link-attachment (citation)
rules that capture the salient features of scholarly citation practice:
Network growth rules
1. System Growth: In each period t, we introduce n(t) new publications, each citing r(t) other publications by way of a
directed link. Hence, the total number of synchronous (backwards) citations produced in period t is C(t) = n(t)r(t),
which grows exponentially at the rate gC = gn + gr.
2. Link Dynamics: illustrated in the schematic Fig. 3(b). For each new publication a ∈n(t):
6
(i) Direct citation a →b: Each new publication a starts by referencing 1 publication b from period tb ≤ta
(where ta = t by definition). The publication b is selected proportional to its attractiveness, prescribed by the weight
Pb,t ≡(c×+cb,t)[n(tb)]α. The factor cb,t is the total number of citations received by b thru the end of period t−1, thereby
representing preferential attachment (PA) link dynamics [31–35]. The factor n(tb) is the number of new publications
introduced in cohort tb, and represents crowding out of old literature by new literature, net of the citation network. The
parameter c× ≡6 is a citation offset controlling for the citation threshold, above which preferential attachment “turns on”
[29] such that a node becomes incrementally more attractive once cb ≥c×.
(ii) Redirection a →{r}b: Immediately after step (i), the new publication a then cites a random number x of
the publications cited in the references list {r}b (of size rb) of publication b. By definition, β represents the fraction of
citations following from this redirection mechanism, which is responsible for the rate of non-spurious triadic closure in the
network. Hence, by construction β = λ/(λ + 1) ∈[0, 1], where λ represents the average number of citations to elements
of {r}b by publication a (such that the expected value of x is λ). Consequently, λ = β/(1 −β) is the ratio of the rate of
citations following citing mechanism (ii) by the rate of citation following the ‘direct’ citation mechanism (i).
We operationalize the stochastic probability of selecting x references according to the binomial distribution,
P(x = k) =
rb
k

(q)k(1 −q)rj−k ,
(4)
with success rate q = λ/rb to ensure that ⟨x⟩= λ. Put another way, on average, the total number of new citations per
period that follow from the redirection citation mechanism (ii) is r(ii)(t) = βr(t).
Once x is determined by way of a random number generator, we then select xBinomial(rb,q) members from the set {r}b (i.e.
without replacement). Each publication belonging to {r}b is selected according to the same weights Pp,t used in step (i).
As such, this second-stage PA also prioritizes more recent elements of {r}b (i.e., those items with larger tp), in addition to
more highly-cited elements of {r}b. Note that we do not allow a to cite any given element of {r}b more than once within
its reference list.
(c) Stop citing after reaching r(t): The referencing process alternates between mechanisms (i) and (ii) until publi-
cation a has cited exactly r(t) publications.
3. Repeat step 2. Link Dynamics for each new publication entering in period t.
4. Update the PA weights, Pp,t, for all existing nodes at the end of each t.
5. Perform steps (1-4) for t = 1...T periods and then exit the network growth algorithm.
3.2.
Computational simulation results
In this section we present the results of a generative citation network model [4] that incorporates latent features of secular
growth and two complementary citation mechanisms illustrated in Fig. 3(b), namely: (i) direct citation from a new publication
a to publication b; and (ii) redirected citations from a to a random number of publications from the reference list of b. The
redirection mechanism (ii) gives rise to triadic closure in the network, thereby capturing shifts in correlated citation practice –
such as the increased ease at which scholars can follow a citation trail with the advent of web-based hyperlinks, as well as self-
citation. This redirection is the dominant contributor to ’consolidation’ measured by Nj in CDp. We explicitly control the rate
of (ii) with a tunable parameter β ∈[0, 1] that determines the fraction of links in the citation network resulting from mechanism
(ii). And to simulate the net effect of β, we construct some networks featuring a constant β(t) = 0 and other networks featuring
an increasing β(t) ≡t/400 such that β(t = 150) = 0.375 corresponding to roughly 1/3 of links arising from mechanism (ii) by
the end of the simulation – see Fig. 3(c).
We construct ensembles of synthetic networks according to six growth scenarios that incrementally add or terminate either of
two citation mechanisms: gr = 0 corresponds to no CI; and β = 0 corresponds to no triadic closure (i.e., no ‘consolidation’).
More specifically, the parameters distinguishing the six scenarios analyzed in what follows are:
(1) no CI (gr = 0 with r(t) = 25); and no explicit redirection mechanism that controls triadic closure (β = 0);
(2) no CI (gr = 0 with r(t) = 25); and an increasing redirection rate, β(t) = t/400 such that β(150) = 0.375;
(3) CI implemented using the empirical value (gr = 0.018) with r(0) = 5; and increasing redirection rate, β(t) = t/400;
(4) same as (3) but calculated using a larger citation window.
(5) same as (3) but reference list capped at r(t) = 25 for t ≥T ∗≡92.
(6) same as (4) but reference list capped at r(t) = 25 for t ≥T ∗.
7
Citation inflation (gr=0.018) and increasing redirection
(β=0.0025) - with citation window CW = 10 years
gr=0.018 and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and No redirection (β=0) - and CW = 5
20
40
60
80
100
120
140
-0.1
0.0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
1.0
Citation inflation (gr=0.018) and increasing redirection
(β=0.0025) - with citation window CW = 10 years
gr=0.018 and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and No redirection (β=0) - and CW = 5
20
40
60
80
100
120
140
0
4
8
12
16
20
24
28
32
36
40
Citation inflation (gr=0.018) and increasing redirection
(β=0.0025) - with citation window CW = 10 years
gr=0.018 and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and No redirection (β=0) - and CW = 5
20
40
60
80
100
120
140
4
8
12
16
20
24
Citation inflation (gr=0.018) and increasing redirection
(β=0.0025) - with citation window CW = 10 years
gr=0.018 and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and β=0.0025 and CW = 5
No reference list citation inflation (gr=0)
and No redirection (β=0) - and CW = 5
20
40
60
80
100
120
140
0.0
0.1
0.2
0.3
[
 pub. c from !tc
Total citations produced per year
Publications per year
References per publication
0
20
40
60
80
100
120
140
100
101
102
103
104
105
100
101
102
103
104
105
c
Model period (year), t
Model period (year), t
Redirection rate, !β(t)
Synthetic citation 
network size
new
publication a 
from 
cohort !
with n(! ) pubs., 
each with
 r(! )
references
ta
ta
ta
!
 = reference list of b
{r}b
 pub. b 
from !tb
(i) = direct
(ii) = redirection (! )
β
!gn = 0.033
!gr = 0.018
!gC = gn + gr = 0.051
a
b
Citation model  
with redirection
Average !CD5(t)
Average rate of extraneous citation, !Rk(t)
20
40
60
80
100
120
140
0.0
0.1
0.2
0.3
!β(t) = t/400
!β(t) = 0
d
f
!gr = 0.018, β (t ) = t /400, C W = 5
!gr = 0.018, β (t ) = t /400, C W = 10
!gr = 0, β (t ) = 0, C W = 5
!gr = 0, β (t ) = t /400, C W = 5
(4) 
(3) 
(2) 
(1)
20
30
40
50
60
8
12
16
20
24
!r (t )
Rk(t )
!R2 = 0.98
!R2 = 0.99
Model period (year), t
Average !CDnok
5
(t)
Average citation rate, !Nij(t)
Model period (year), t
e
g
, !C(t)
, !n(t)
, !r(t)
FIG. 3:
Numerical simulation of growing citation networks elucidates roles of citation inflation and strategic citation practice. (a)
Model system evolved over T = 150 periods (representing years), using growth parameters estimated for the entire Clarivate Analytics Web
of Science citation network [4]. (b) Schematic of the citation model comprised of two citing mechanisms: (i) direct citations, and (ii) redirected
citations made via the reference list {r}b of an intermediate item b. Type (ii) references give rise to triadic closure corresponding to the Nj
factor in CDp. (c) The rate of type (ii) references is controlled by the parameter β(t), which quantifies the fraction of links in the citation
network directly following this ‘consolidation’ mechanism [1, 3], which yields more negative CDp values. To disentangle the roles of citation
inflation (owing to gr > 0) from shifts in scholarly citation practice (owing to ∂tβ(t) > 0), we compare four scenarios: scenarios (1,2)
(gray and black curves) feature no citation inflation (gr = 0); (2,3) compare β(t) = 0 and β(t) = t/400; and (3,4) (cyan and blue curves)
compare the effects of different citation windows (CW). (d) Each curve is the average CDCW (t) calculated for a single synthetic network.
(e) Average CDnok
5 (t). (f) Rk(t) is the average rate of extraneous citations, which increases as either r(t) or CW increase. (inset) High linear
correlation between r(t) and Rk(t) shows that the decreasing trend in CD(t) is largely attributable to citation inflation. (g) The average value
of Nij(t) = Ni + Nj (which defines the denominator of CDnok) also systematically increases, and so neglecting the term Nk does not solve
the fundamental issue of CI.
For each scenario we constructed four distinct synthetic citation networks, each evolving over t ∈[1, T = 150] periods (i.e
years) from a common initial condition at t = 0. For scenarios (1-3) we calculate CDp using a citation window of CW= 5
periods, whereas in (4) we use CW=10 periods. Scenarios (3) and (4) are shown in order to show the non-linear sensitivity of
CDCW to the CW parameter [36], and demonstrates that fixed CWs do not address CI [5].
Figure 3(d) shows 16 average CD(t) curves calculated for each synthetic network. Because the sources of network variation
are strictly limited to the stochastic link dynamics, there is relatively little variance across each ensemble of networks constructed
using the same scenario parameters, and so in what follows we show all realizations simultaneously. As there are no latent
institution, author or other innovation covariates, then the difference between network ensembles is attributable to either CI or
the redirection mechanism.
We start by considering scenarios (1,2) for which gr = 0, which show that CD5(t) systematically increases in the absence of
reference list CI. While scenario (1) does capture CI attributable to increased publication volume (gn > 0), it does not appear to
be sufficient to induce a negative trend in CD5(t). Scenario (2) features an increasing β(t), which results in larger CD values
because redirected citations tend to fall outside shorter CW and thus are not incorporated into the CD subgraph. Summarily,
comparison of (1) and (2) indicate that the redirection mechanism capturing shifting patterns of scholarly citation behavior is the
weaker of the two mechanisms we analyzed.
The comparison of scenarios (2,3) illustrates the role of CI. Notably, scenario (3) reproduces both the magnitude and rate
of the decreasing trend in CD(t) observed for real citation networks [3]. Figure 3(e) shows that alternative metric CDnok
5
proposed in ref. [22], which also matches the empirical trends reported in ref. [3]. These results demonstrate the acute effect of
reference-list CI on CD since the only difference between scenarios (2) and (3) pertains to gr.
Figure 3(f) reproduces the linear relationship between r(t) and Rk(t) and confirms the empirical relationship shown in Fig.
2(e) – thereby solving the mystery regarding the origins of the decreasing disruptiveness over time [25]: as the size of the
reference list {r}p increases, so does the likelihood that {r}p contains a highly-cited paper, which increases Nk to such a degree
8
Scenario (6): CW = 10 years
Scenario (5): CW = 5
Scenario (4): CW = 10 years
Scenario (3): CW = 5
20
40
60
80
100
120
140
0.0
0.1
0.2
0.3
Scenario (6): CW = 10 years
Scenario (5): CW = 5
Scenario (4): CW = 10 years
Scenario (3): CW = 5
20
40
60
80
100
120
140
4
8
12
16
20
24
Total citations produced per year
Publications per year
References per publication
0
20
40
60
80
100
120
140
100
101
102
103
104
105
100
101
102
103
104
105
10
20
4
8
12
16
b
c
T* = 92
Average !CD5(t)
Average !Rk(t)
Rk(t)
!r (t )
Model period (year), t
T* = 92
Network parameter scenarios
!R2 = 0.97
!R2 = 0.99
gr = 0.018
gr = 0
Network size 
a
T* = 92
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
0.0
0.1
0.2
d
!Pt(CD5)
e
Scenario (5):
t = [1-10]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [11-20]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [21-30]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [31-40]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [41-50]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [51-60]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [61-70]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [71-80]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [81-90]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [91-100]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [101-110]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [111-120]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [121-130]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [131-140]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
t = [141-145]
-0.2
0.0
0.2
0.4
0.6
0.8
1.0
Probability Density Function by period t, !Pt(CD5)
Disruption Index, !CD5
Disruption Index, !CD5
β(t) = t /400, C W = 5
!gr = 0.018  for  t < 92;
!gr = 0  and  r(t) = 25  for  t ≥92
(4) 
(3) 
(6) 
(5) 
gr = 0.018, C W = 5
gr = 0.018, C W = 10
gr = 0.018, T* = 92, C W = 5
gr = 0.018, T* = 92, C W = 10
FIG. 4: Hypothetical publishing policy intervention reveals effect of capped reference list lengths on CD. (a) Evolution of network size
in scenarios (5,6) where the number of references per paper is capped at r(t ≥T ∗) = 25 after T ∗= 92, such that the growth in the total
citations produced per year depends solely on the growth of n(t). (b) Average CDCW (t) for scenarios (3)-(6). Immediately after T ∗= 92
the CD(t) trends for intervention scenarios (5,6) reverse from decreasing to increasing. (c) The divergence in CD(t) trends is attributable to
the taming of CI which stabilizes Rk(t). (d) The frequency distribution Pt(CD5) aggregated over 10-period intervals indicated by the color
gradient; vertical dashed lines indicate distribution mean. Comparing with Fig. A2(a), it is clear that the Pt(CD5) distribution for Scenario (5)
becomes significantly more stable t ≥T ∗, with variation due to the residual citation inflation associated with publication volume growth (gn).
(e) The stability of the Pt(CD5) distribution after T ∗suggests that quantitative properties of the Extreme Value (Fisher-Tippett) distribution
could be used to develop time-invariant disruption measures; orange curves represent the best-fit Fisher-Tippett distribution model.
that Rk,p ≫1 and so CDp →0 independent of the relative differences between disruption and consolidation captured by
Ni −Nj. Figure 3(g) shows that even CDnok
5
suffers from systematic bias affecting its denominator, and so neglecting the term
Nk does not solve the fundamental issue of CI.
Scenarios (3,4) reveal the effect of CW, which controls the size of the set {c}p and thus the magnitude and growth rate of
Rk(t). Notably, the number of items included in {c}p depends on both CW and t because the reference age between the cited
and citing article increases with time [4]. Regardless, the average CDCW (t) →0 as r(t) increases, independent of the CW
used.
9
Figure 4 further explores the implications of CI on CD by modeling a hypothetical scenario in which CI is suddenly ‘turned
off’ after a particular intervention time period T ∗. In this way, scenarios (5,6) explore the implications of a restrictive publishing
policy whereby all journals suddenly agree to impose caps on reference list lengths. Scenarios (5,6) enforce this hypothetical
policy at t ≥T ∗≡92 by way of a piecewise smooth r(t) curve such that: r(t) = r(0) exp[grt] for t < T ∗and r(t) = r(T ∗) =
25 – see Fig. 4(a). This hypothetical intervention exhibits the potential for the scientific community to temper the effects of CI
by way of strategic publishing policy. For completeness, scenarios (3) and (5) use CW=5 and scenarios (4) and (6) use CW =10.
Figures 4(b,c) show that the average CD(t) and Rk(t) trajectories for each pair of scenarios are indistinguishable prior to
T∗. Yet immediately after T∗the scenarios (5) and (6) diverge from (3) and (4), respectively. Notably, the average CD5(t)
in scenarios (5) and (6) reverse to the point of slowly increasing, thereby matching the trends observed for scenario (2). In the
spirit of completeness, Fig. 4(c) confirms that this trend-reversal is due to the relationship between r(t) and Rk(t). The shifts
in the average CD5(t) are indeed representative of the entire distribution of CDp,5 values – see Figs. 4(d,e). Interestingly,
the distribution Pt(CD5) converges to a stable Extreme-Value (Fisher-Tippett) distribution in the absence of reference list
growth, which exposes candidate avenues for developing time-invariant measures of disruption by rescaling values according
to the location and scale parameters. The feasibility of this approach was previously demonstrated in an effort to develop
field-normalized [28] and time-invariant (z-score) citation metrics [37, 38].
4.
Discussion
In summary, Despite the reasonable logic behind the definition of CD, the difference between disruptive and consolidating
links appearing in the numerator, Ni −Nj, is systematically overwhelmed by the extensive quantity Rk ∼r(t) appearing
in the denominator of CD. More specifically, we show that the CD index artificially decreases over time due to citation
inflation deriving from ever-increasing r(t), rendering CD systematically biased and unsuitable for cross-temporal analysis.
For the same reasons that central banks must design monetary policy to avoid the ill effects of printing excess money [6,
7], researchers analyzing scientific trends should be wary of citation-network bibliometrics that are not stable with respect to
time. Scenarios where achievement metrics are non-stationary and thus systematically biased by nominal inflation are common,
including researcher evaluation [12], journal impact factors [39], and even achievement metrics in professional sports [40, 41].
In addition to the measurement error induced by CI, the disruption index also does not account for confounding shifts in
scholarly citation practice. The counterbalance to disruption, captured by the term Ni in Eq. (1), is consolidation (Nj), which
is fundamentally a measure of triadic closure in the subgraph Gp. While triangles may spuriously occur in a random network,
their frequency in real networks is well in excess of random base rates due to the correlated phenomena underlying the scholastic
practice – in particular, increasingly strategic (personal and social) character of scholarly citing behavior.
The source and implications of citation inflation are not inherently undesirable, and if anything point to thriving industry
emerging from the scientific endeavor. The advent of online-only journals is a main reason for the steady increase in r(t), as
they are not limited by volume print capacity, unlike more traditional print journals. Hence, in the era of megajournals [14] there
may have emerged a tendency to cite more liberally than in the past. Another mechanism connecting CI and citation behavior
derives from the academic profession becoming increasingly dominated by quantitative evaluation, which thereby promotes the
inclusion of strategic references dispersed among the core set of references directly supporting the research background and
findings [42]. Notably, scholars have identified various classes of self-citation [43], which generally emerge in order to benefit
either the authors [44–46], institutional collectives [47], the handling editor [14], and/or the journal [48, 49] – but are otherwise
difficult to differentiate from ‘normal’ citations. Regardless of their intent, these self-citations are more likely to contribute to
triadic closure because if article b cites c as a result of self-citation, then for the same reason a new article a that cites b (or c) is
that much more likely to complete the triangle on principal alone.
These two issues – citation inflation and shifting scholarly behavior – introduce systematic bias in citation-based research
evaluation that extends over significant periods of time. Indeed, time is a fundamental confounder, and so to address this
statistical challenge various methods introducing time-invariant citation metrics have been developed [5, 28, 29, 38]. A broader
issue occurs when different variables simultaneously shift over time, such as the number of coauthors, topical breadth and depth
of individual articles, which makes establishing causal channels between any two variables ever more challenging. By way of
example, we analyzed the relationship between CDp and kp, using a regression model with fixed effects for publication year to
superficially control for secular growth, and observe a positive relationship between these two quantities, in stark contrast to the
negative relationship reported in ref. [2].
We conclude with a policy insight emerging from our analysis regarding interventional approaches to addressing citation
inflation. Namely, journals might consider capping reference lists commensurate with the different types of articles they publish,
e.g. letters, articles, reviews, etc. An alternative that is more flexible would be to impose a soft cap based upon the average
number of references per article page [16]. Results of our computational simulations indicate that such policy could readily
temper the effects of citation inflation in research evaluation, and might simultaneously address other shortcomings associated
with self-citations by effectively increasing their cost.
10
Data Availability
All synthetic citation networks analyzed are openly available at the Dryad data repository [30]. The psuedocode for the citation
network growth is sufficient to generate additional citation networks with different parameters.
[1] Funk, R. J. & Owen-Smith, J. A dynamic network measure of technological change. Management science 63, 791–817 (2017).
[2] Wu, L., Wang, D. & Evans, J. A. Large teams develop and small teams disrupt science and technology. Nature 566, 378–382 (2019).
[3] Park, M., Leahey, E. & Funk, R. J. Papers and patents are becoming less disruptive over time. Nature 613, 138–144 (2023).
[4] Pan, R. K., Petersen, A. M., Pammolli, F. & Fortunato, S. The memory of science: Inflation, myopia, and the knowledge network. Journal
of Informetrics 12, 656–678 (2018).
[5] Petersen, A. M., Pan, R. K., Pammolli, F. & Fortunato, S. Methods to account for citation inflation in research evaluation. Research
Policy 48, 1855–1865 (2018).
[6] Orphanides, A. & Solow, R. M. Money, inflation and growth. Handbook of monetary economics 1, 223–261 (1990).
[7] Orphanides, A. The quest for prosperity without inflation. Journal of monetary Economics 50, 633–663 (2003).
[8] Wuchty, S., Jones, B. F. & Uzzi, B. The increasing dominance of teams in production of knowledge. Science 316, 1036–1039 (2007).
[9] Petersen, A. M., Pavlidis, I. & Semendeferi, I. A quantitative perspective on ethics in large team science. Sci. & Eng. Ethics. 20, 923–945
(2014).
[10] Pavlidis, I., Petersen, A. M. & Semendeferi, I. Together we stand. Nature Physics 10, 700–702 (2014).
[11] Bornmann, L. & Daniel, H.-D. What do citation counts measure? a review of studies on citing behavior. Journal of documentation
(2008).
[12] Petersen, A. M., Wang, F. & Stanley, H. E. Methods for measuring the citations and productivity of scientists across time and discipline.
Physical Review E 81, 036114 (2010).
[13] Shen, H.-W. & Barab´asi, A.-L. Collective credit allocation in science. Proceedings of the National Academy of Sciences 111, 12325–
12330 (2014).
[14] Petersen, A. M. Megajournal mismanagement: Manuscript decision bias and anomalous editor activity at PLOS ONE. Journal of
Informetrics 13, 100974 (2019).
[15] S´anchez-Gil, S., Gorraiz, J. & Melero-Fuentes, D. Reference density trends in the major disciplines. Journal of informetrics 12, 42–58
(2018).
[16] Abt, H. A. & Garfield, E. Is the relationship between numbers of references and paper lengths the same for all sciences? Journal of the
American Society for Information Science and Technology 53, 1106–1112 (2002).
[17] Dai, C. et al. Literary runaway: Increasingly more references cited per academic research article from 1980 to 2019. Plos one 16,
e0255849 (2021).
[18] Nicolaisen, J. & Frandsen, T. F. Number of references: A large-scale study of interval ratios. Scientometrics 126, 259–285 (2021).
[19] Sinha, A. et al. An overview of Microsoft Academic Service (MAS) and applications. In Proceedings of the 24th international conference
on world wide web, 243–246 (2015).
[20] Nakamoto, H. Synchronous and diachronous citation distributions. In Egghe, L. & Rousseau, R. (eds.) Informetrics 87/88: Select
Proceedings of the 1st International Conference on Bibliometrics and Theoretical Aspects of Information Retrieval, 157–163 (Elsevier,
New York, 1988).
[21] Gl¨anzel, W. Towards a model for diachronous and synchronous citation analyses. Scientometrics 60, 511–522 (2004).
[22] Bornmann, L., Devarakonda, S., Tekles, A. & Chacko, G. Are disruption index indicators convergently valid? The comparison of several
indicator variants with assessments by peers. Quantitative Science Studies 1, 1242–1259 (2020).
[23] Wu, S. & Wu, Q. A confusing definition of disruption. SocArXiv e-print: 10.31235/osf.io/d3wpk (2019).
[24] Leydesdorff, L., Tekles, A. & Bornmann, L. A proposal to revise the disruption index. El profesional de la informaci´on (EPI) 30 (2021).
[25] Kozlov, M. ’disruptive’science has declined-and no one knows why. Nature (2023).
[26] Krapivsky, P. L. & Redner, S. Network growth by copying. Phys. Rev. E 71, 036118 (2005).
[27] Barabasi, A. Network Science (Cambridge University Press, 2016).
[28] Radicchi, F., Fortunato, S. & Castellano, C. Universality of citation distributions: Toward an objective measure of scientific impact. Proc.
Natl. Acad. Sci. USA 105, 17268–17272 (2008).
[29] Petersen, A. M. et al. Reputation and impact in academic careers. Proc. Natl. Acad. Sci. USA 111, 15316–15321 (2014).
[30] Petersen, A. M. The disruption index suffers from citation inflation and is confounded by shifts in scholarly citation practice: synthetic
citation networks for bibliometric null models. https://datadryad.org/stash/dataset/doi:10.6071/M3G674 (2023).
[31] Simon, H. A. On a class of skew distribution functions. Biometrika 42, 425–440 (1955).
[32] Barabasi, A.-L. et al. Evolution of the social network of scientific collaborations. Physica A 311, 590 – 614 (2002).
[33] Jeong, H., Neda, Z. & Barabasi, A. L. Measuring preferential attachment in evolving networks. EPL 61, 567 (2003).
[34] Redner, S. Citation statistics from 110 years of physical review. Physics Today 58, 49–54 (2005).
[35] Peterson, G. J., Presse, S. & Dill, K. A. Nonuniversal power law scaling in the probability distribution of scientific citations. Proc. Natl.
Acad. Sci. USA 107, 16023–16027 (2010).
[36] Bornmann, L. & Tekles, A. Disruption index depends on length of citation window. El profesional de la informaci´on (EPI) 28 (2019).
[37] Petersen, A. M. & Penner, O. Inequality and cumulative advantage in science careers: a case study of high-impact journals. EPJ Data
Science 3, 24 (2014).
[38] Petersen, A. M., Ahmed, M. E. & Pavlidis, I. Grand challenges and emergent modes of convergence science. Humanities and Social
11
Sciences Communications 8, 194 (2021).
[39] Althouse, B. M., West, J. D., Bergstrom, C. T. & Bergstrom, T. Differences in impact factor across fields and over time. JASIST 60,
27–34 (2009).
[40] Petersen, A. M., Penner, O. & Stanley, H. E. Methods for detrending success metrics to account for inflationary and deflationary factors.
The European Physical Journal B 79, 67–78 (2011).
[41] Petersen, A. M. & Penner, O. Renormalizing individual performance metrics for cultural heritage management of sports records. Chaos,
Solitons & Fractals 136, 109821 (2020).
[42] Abramo, G., D’Angelo, C. A. & Grilli, L. The effects of citation-based research evaluation schemes on self-citation behavior. Journal of
Informetrics 15, 101204 (2021).
[43] Ioannidis, J. P. A generalized view of self-citation: Direct, co-author, collaborative, and coercive induced self-citation. Journal of
psychosomatic research 78, 7–11 (2015).
[44] Fowler, J. & Aksnes, D. Does self-citation pay? Scientometrics 72, 427–437 (2007).
[45] Ioannidis, J. P., Baas, J., Klavans, R. & Boyack, K. W. A standardized citation metrics author database annotated for scientific field. PLoS
biology 17, e3000384 (2019).
[46] Pinheiro, H., Durning, M. & Campbell, D. Do women undertake interdisciplinary research more than men, and do self-citations bias
observed differences? Quantitative Science Studies 3, 363–392 (2022).
[47] Tang, L., Shapira, P. & Youtie, J. Is there a clubbing effect underlying c hinese research citation increases? Journal of the Association
for Information Science and Technology 66, 1923–1932 (2015).
[48] Martin, B. R. Editors’ JIF-boosting stratagems–Which are appropriate and which not? Research Policy 45, 1–7 (2016).
[49] Ioannidis, J. P. & Thombs, B. D. A user’s guide to inflated and manipulated impact factors. European journal of clinical investigation
49, e13151 (2019).
[50] Egghe, L. A model showing the increase in time of the average and median reference age and the decrease in time of the price index.
Scientometrics 82, 243–248 (2010).
[51] Lariviere, V., Archambault, E. & Gingras, Y. Long-term variations in the aging of scientific literature: From exponential growth to
steady-state science (1900-2004). JASIST 59, 288–296 (2008).
[52] Acharya, A. et al. Rise of the Rest: The Growing Impact of Non-Elite Journals. arXiv:1410.2217 (2014).
[53] Schwartz, C. A. The Rise and Fall of Uncitedness. College & Research Libraries 58, 19–29 (1997).
[54] Wallace, M. L., Lariviere, V. & Gingras, Y. Modeling a century of citation distributions. Journal of Informetrics 3, 296 – 303 (2009).
[55] Lariviere, V., Gingras, Y. & Archambault, E. The decline in the concentration of citations, 1900-2007. JASIST 60, 858–862 (2009).
[56] Parolo, P. D. B. et al. Attention decay in science. Journal of Informetrics 9, 734 – 745 (2015).
[57] Barabasi, A. L., Song, C. & Wang, D. Publishing: Handful of papers dominates citation. Nature 491, 40 (2012).
12
A1.
Appendix: Reproduction of statistical regularities in a real-world citation
network – the Web of Science
The following is a summary of the structural and dynamical regularities that characterize a typical network produced by our
model using the growth parameters indicated along the top bar of Fig. A1. In addition to the stylized regularities listed below,
the citation model also reproduces the temporal trends in CD5, CDnok
5 , and the frequency distribution P(CD5), reported by
Park et al. [3] – see Figs 1, A1 and A2.
Figure A1(a) shows the time series n(t), r(t), and R(t) as determined by the empirical parameters gn, gr, and gR.
Figure A1(b) shows the mean of the reference distance ∆r = ta−tp calculated as the time difference between the publication
year of a and of any given publication p that it cites. The increasing ⟨∆r|t⟩conforms with prior theoretical and empirical work
[4, 50–52].
Figure A1(c) shows the decreasing frequency of publications with less than C = 0, 1, 2,5, 10 citations. This trend is consistent
with empirical work [53–55], and has profound implications on the connectivity of the citation network, and search and retrieval
algorithms based upon the connectivity.
Figure A1(d) shows the average citation life-cycle, ∆c(τ|t) of individual publications conditioned on their publication year
t, where τ is the age of the publication in that year, τp = t −tp + 1. The exponential decay of the consistent with empirical
work [56].
Figure A1(e) shows the mean and standard deviation of c′ = ln(cp + 1), where citations counts cp are tallied at T, the
final period of the model. Naturally, very recent publications have not had sufficient time to accrue citations. Also, very early
publications were at the peak of their lifecycle during periods in which there was smaller n(t). Hence, the average µLN peaks
near the end of the model, and then decays to 0 for the final period. This systematic bias due to citation inflation, as well as
the right-censoring bias, may seem difficult to overcome. However, the location and scale given by µLN and σLN, respectively,
provide a powerful solution, which is to normalized citations according to the rescaling,
zp,t = ln(cp,t + 1) −µLN,t
σLN,t
,
(A1)
where µLN,t = ⟨ln(cp,t + 1)⟩and σLN,t = σ[ln(cp,t + 1)] are the mean and the standard deviation of the logarithm of cp,t + 1
calculated across all p within each t. This normalization procedure leverages the property that the distribution P(ct|t) is log-
normally distributed, as shown for real citation networks [28]. As such, the distribution P(zt) takes the form of a standardized
z-score distributed according to the normal distribution N(0, 1), which is stable over time. As shown in Fig. A1(f), P(z) forms
an inverted parabola when plotted on log-linear axes, independent of t. This normalization is useful in regression settings aimed
at identifying citation effects net of temporal trends, where t is included in the model specification as either as a continuous or
dummy variable [5, 38].
Figures A1(g,h) show the evolution of the citation share of the top and bottom percentile groups FP c(Q|τ, t), consistent with
empirical work showing that a small fraction of the top-cited papers from high-impact journals increasingly dominate the future
citations of that journal [57].
And Figure A1(i) shows individual citation trajectories, cp,t, produced by the model. The shape and distribution of the cohort
are consistent with empirical citation trajectories reported in [29].
13
60
90
120
150
180
0
1
2
3
-4
-2
0
2
4
10-4
10-3
10-2
10-1
NH0,1L
171-190
151-170
131-150
111-130
91-110
71-90
51-70
0
30
60
90
120
150
180
0.0
0.2
0.4
0.6
0.8
1.0
0
30
60
90
120
150
180
2
4
6
8
10
0
10
20
30
40
50
60
10-3
10-2
10-1
100
170
180
190
100
101
102
200
180
150
120
90
60
30
1
0
10
20
30
0.00
0.02
0.04
0.06
0.08
180
175
170
165
160
155
150
0
10
20
30
0.0
0.1
0.2
0.3
0.4
0.5
0.6
30
60
90
120
150
180
100
101
102
103
104
105
Citation life cycle
 ⟨Δc(τ | t )⟩
MC period, t
MC period, t
references per paper, r(t)
number of papers, n(t)
total references, R(t)---
cohort age, τ
Mean reference
 distance, ⟨𝛥r | t⟩
normalized (log-normal) citations, zt
PDF,  P(zt)
System size
T=200, N(T) = 218,698 papers, R(T) = 5,025,106, n(0)=10, gn = 0.033,  r(0)=1, gr=0.018, α=5, β=1/5, cx = 6
cohort age, τ
MC period, t
Citation share 
F∑c(top 1%|τ, t)  
C=0
C=1
C=2
C=5
C=10
Uncited fraction
F (c ≤ C | t) 
a
c
d
f
0
30
60
90
120
150
180
10-3
10-2
10-1
100
200
180
160
140
120
100
80
60
40
20
1
Citation share 
F∑c(bottom 75%|τ, t)  
MC period, t
MC period, t
cohort age, τ
μLN

σLN
Log-Normal location μ
 and scale  σ
Cumulative citation
 trajectory, c
g
h
i
b
e
t{
t{
p}
t{
p,t
FIG. A1: Citation redirection model – reproduction of empirical statistical regularities that characterize real citation patterns. Figure
and caption reproduced with permission from Pan et al. [4]. Shown are various properties of the synthetic citation network that can be
compared with empirical trends. We evolved the simulation using the parameters: T ≡200 MC periods (∼years), n(0) ≡10 initial
publications, r(0) ≡1 initial references, exponential growth rates gn ≡0.033 and gr ≡0.018, secondary redirection parameter β ≡1/5
(corresponding to λ = 1/4), citation offset C× ≡6, and life-cycle decay factor α ≡5. At the final period t = T, the final cohort has size
n(T) = 7112 new publications, r(T) = 35 references per publication, and final citation network size N(200) = 218,698 publications (nodes)
and R(T) = 5,025,106 total references/citations (links). (a) The size of the system in each MC period t. (b) Growth of the mean reference
distance ⟨∆r⟩. (c) The fraction fc≤C(t|τ = 5) of publications which have C or less citations at cohort age τ = 5. (d) The citation life cycle,
measured here by the mean number of new citations τ periods after entry (publication). The different curves correspond to the publication
cohort entry period t. For sufficiently large t the life cycle decays exponentially. (e) Growth of the logarithmic mean (location) value µLN,t
and the relative stability of the logarithmic standard deviation (scale) value σLN,t. µLN,t = ⟨log(cp,t)⟩and σLN,t = σ[log(cp,t)] are the
logarithmic mean and standard deviation calculated across all p within each age cohort t. (f) The distribution P(zp,t) of the normalized citation
impact zp,t. For visual comparison we plot the Normal distribution N(µ = 0, σ = 1). (G) The increasing citation share fP c – the fraction
of the total citations received by all publications from cohort t – of the top 1% of publications from cohort t (ranked at cohort age τ = 10).
(h) The decreasing citation share fP c of the bottom 75% of publications. (i) The cumulative citation count cp(t) of the top 200 publications
(p) from the interval t = [170, 179], ranked according to cp(t = 180). The dashed line represents the average citations for p from the same
cohort over the same period.
14
a
￼Pt(CD5)
b
Scenario (3):
￼gr = 0.018, β(t) = t/400, CW = 5
t = [1-10]
-1.0
-0.5
0.0
0.5
1.0
t = [11-20]
-1.0
-0.5
0.0
0.5
1.0
t = [21-30]
-1.0
-0.5
0.0
0.5
1.0
t = [31-40]
-1.0
-0.5
0.0
0.5
1.0
t = [41-50]
-1.0
-0.5
0.0
0.5
1.0
t = [51-60]
-1.0
-0.5
0.0
0.5
1.0
t = [61-70]
-1.0
-0.5
0.0
0.5
1.0
t = [71-80]
-1.0
-0.5
0.0
0.5
1.0
t = [81-90]
-1.0
-0.5
0.0
0.5
1.0
t = [91-100]
-1.0
-0.5
0.0
0.5
1.0
t = [101-110]
-1.0
-0.5
0.0
0.5
1.0
t = [111-120]
-1.0
-0.5
0.0
0.5
1.0
t = [121-130]
-1.0
-0.5
0.0
0.5
1.0
t = [131-140]
-1.0
-0.5
0.0
0.5
1.0
t = [141-145]
-1.0
-0.5
0.0
0.5
1.0
-1.0
-0.6
-0.2
0.2
0.6
1.0
0.0
0.2
0.4
0.6
Probability Density Function by period t, ￼Pt(CD5)
Disruption Index, ￼CD5
Disruption Index, ￼CD5
-1.0
-0.6
-0.2
0.2
0.6
1.0
0.0
0.2
0.4
0.6
￼Pt(CDnok
5
)
Alternative Disruption Index, ￼CDnok
5
c
FIG. A2: The distribution of CD5 derived from synthetic citation networks follows the Extreme Value (Fisher-Tippett) distribution
but is not stable over time. (a) The probability density function Pt(CD5) is calculated using values aggregated over 10-period intervals
indicated by t, with color gradient indicating each 10-period interval. Vertical dashed lines indicate distribution mean. (b) Each 10-period
Pt(CD5) is shown with the best-fit Extreme Value (Fisher-Tippett) distribution (orange curve), estimated using Mathematica 13.1 algorithm
FindDistribution. The Extreme Value distribution is a better fit as t increases, pointing to a strategy for normalizing CD5 that supports cross-
temporal analysis in the same way that the properties of the log-normal distribution can be used to normalize citation counts collected over
different periods [5, 29, 38]. (c) Distribution of an alternative disruption index, Pt(CDnok
5 ), calculated using same temporal periods as in (a),
shows that the vast majority of publications according to this measure are highly disruptive.
