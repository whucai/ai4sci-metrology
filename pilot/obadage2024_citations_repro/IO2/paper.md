# CAN CITATIONS TELL US ABOUT A PAPER’S REPRODUCIBILITY? A CASE STUDY OF MACHINE LEARNING PAPERS

Rochana R. Obadage   
Old Dominion University   
Norfolk, VA, USA   
oruma001@odu.edu

Sarah M. Rajtmajer IST, Pennsylvania State University University Park, PA, USA smr48@psu.edu

Jian Wu   
Old Dominion University   
Norfolk, VA, USA   
j1wu@odu.edu

# ABSTRACT

The iterative character of work in machine learning (ML) and artificial intelligence (AI) and reliance on comparisons against benchmark datasets emphasize the importance of reproducibility in that literature. Yet, resource constraints and inadequate documentation can make running replications particularly challenging. Our work explores the potential of using downstream citation contexts as a signal of reproducibility. We introduce a sentiment analysis framework applied to citation contexts from papers involved in Machine Learning Reproducibility Challenges in order to interpret the positive or negative outcomes of reproduction attempts. Our contributions include training classifiers for reproducibility-related contexts and sentiment analysis, and exploring correlations between citation context sentiment and reproducibility scores. Study data, software, and an artifact appendix are publicly available at https: // github. com/ lamps-lab/ ccair-ai-reproducibility .

Keywords Citation Contexts · Reproducibility · Machine Learning · Sentiment Analysis · Science of Science

# 1 Introduction

In the rapidly advancing fields of machine learning (ML) and artificial intelligence (AI), emerging technologies are often advancements, refinements, or assemblies of existing ones. Because of this, reproducibility is central to progress in these fields. Yet, the growing complexity of ML research, hardware and software resource constraints, code and data with insufficient documentation, proprietary datasets, and current incentive structures have made the direct reproduction of existing models and findings infeasible in many cases. Indeed, the ML/AI community is beginning to demonstrate that it too faces a crisis of reproducibility [1, 2]. Directly reproducing reported results is the most reliable method to test the reproducibility of a paper, but this method does not scale to millions of research papers. Existing efforts to automatically assess reproducibility and replicability either use shallow features directly extracted from paper content, such as bibliographic, statistical, and semantic features [3], or latent features such as word embeddings [4]. As yet, no automatic approach to reproducibility or replicability assessment has demonstrated good enough performance to be useful in real-world scenarios.

Our work explores opportunities to mine the text around downstream citations of a paper–citation context (Figure 1)–for cues indicating that an author has successfully or unsuccessfully replicated another paper’s work in the course of their own. This is motivated by an understanding that most reproductions and replications are relatively informal (vs. explicitly framed as a replication study) and occur commonly in ML/AI in service to model comparisons against benchmarks, use of one technology in service to a different research aim, or similar. The reproducing or replicating author will note this in their own work, information which–if reliably extracted–could be a rich resource for understanding reproducibility and replicability in the field. Although prior research has performed classification on citation contexts for various purposes [5, 6, 7, 8], whether citation context can be used as a signal of reproducibility has

Tian, Chen, and Ganguli (2o21) showed that a regularizer is essential for the existence of the non-collapsed solution. In this paper, we make a first attempt towards the second question, by studyinga familyofalgorithmsnamedDirectSet，inwhichtheDirectPred algorithm proposed by Tian et al. (2o21) isaspecial case with positive Although we tried to train split network with the same training data weused,we failed to reproduce their results and used the model trained by theauthors[32]. negative not yet been studied. In this paper, we address this question by exploring the correlation between reproducibility scores and reproducibility sentiment of citation context.

Specifically, we train ML models to classify citation contexts based on their reproducibility-based sentiment. This approach falls under the umbrella of aspect-based sentiment analysis, a text analysis technique that classifies text by sentiment related to a given aspect [11]. Reproducibility scores are calculated based on the reports of direct reproducibility studies. We then study whether the reproducibility score is correlated with the normalized citation context count of a certain sentiment. Our contributions are as follows:

1. We observe a correlation between reproducibility scores and citation context sentiment in a pilot dataset containing 41,244 citation contexts extracted from 130 ML papers.   
2. We build the first ground truth dataset of direct reproducibility scores of 22 ML papers and 1937 citation contexts, manually labeled into three reproducibility sentiment categories.   
3. We train and validate two ML models to classify citation context into reproducibility sentiments and obtain F1-scores ranging from 0.70 to 0.86.

# 2 Related Work

Our study is related to prior work on reproducibility of ML and AI. While Gundersen et al. [12] discuss state-ofthe-art of reproducibility in AI, Raff [1] evaluates the reproducibility of 255 papers published between 1984 to 2017, emphasizing the importance of factors beyond code availability. Akella et al. [13] discuss factors that contribute to reproducibility of ML findings and propose solutions.

We build upon work in sentiment analysis. Yousif et al. [14] propose a multitask learning model based on convolutional and recurrent neural networks that perform the citation sentiment and purpose classification. HuggingFace [15] contains a repository of open-source ML models for sentiment analysis tasks trained on various datasets. We used both supervised and unsupervised models trained on different datasets including tweets, social media posts, and citation contexts.

In terms of citation context classification, Cohan et al. [16] propose “structural scaffolds", a multitask model incorporating structural information of scientific papersfor classification of citation intent. Te et al. [8] compare methods for classification of critical vs. non-critical citation contexts. Budi et al. discuss citation meaning using sentiment, role, and citation function classifications [17].

# 3 Dataset

The dataset contains three types of scientific documents: original studies - original research papers/findings which serve as targets for a reproduction; reproducibility studies (rep-studies) - papers reporting attempts to reproduce a particular paper/finding; and, citing papers - papers that cite the original studies. We prepared our dataset in five steps (see Figure 2).

1. Collect reproducibility studies from existing data sources

# Can citations tell us about a paper’s reproducibility? A case study of machine learning papers

2. Collect metadata for original studies   
3. Calculate the reproducibility score for each rep-study   
4. Collect citation contexts from citing papers   
5. Label citation contexts by reproducibility sentiments

# 3.1 Reproducibility Studies

We collected the metadata for 145 rep-studies from existing data sources listed in Table 1. The Machine Learning Reproducibility Challenges (MLRC) contains 129 rep-studies of 114 papers (some rep-studies were conducted on the same original paper). Because the majority of papers were successfully reproduced, we supplement the data with 16 rep-studies by Ajayi et al. [18] including 5 successful and 11 unsuccessful rep-studies. The same input data, computational steps, methods, and analysis conditions were adopted in all rep-studies except that the experiments were conducted by different teams. Using the DOIs we collected metadata for all the 130 original studies from the Semantic Scholar Graph API (S2GA; [19]).

Re. Re. from MLRC </> rep-study #rep45udies   
PDF. competitions √   
PF > cited paper riginal stepdy fram # 1ginal studies ↓   
citing citing citing -citations the citinal 13,314   
paper paper paper study (S2GA) #citing papers ↓ ↓ ↓   
context x1 contexty1 context z possible multiple   
context x2 context y2 context z2 records per each 41,244   
context x context yn context Zn citation #citation contexts context x :'positive' labeled citation contexty2:'negative' contexts from 22 1,937 context z :'neutral' cited papers #labeled contexts

# 3.2 Reproducibility Score Calculation

Traditionally, reproducibility scores are defined as dichotomous values, indicating reproducibility of a paper based on its primary finding. Here, we introduce an extended reproducibility score (rs_score) for a paper with multiple findings, given by the equation below. To calculate it, we perused full text of replication studies. The rs_score distribution is shown in Table 2.

# 3.3 Citation Context Collection

We collected all citation contexts available for each of 130 original studies from S2GA [19] (Table 1). We collected 13,314 citations and 41,244 citation contexts. On average, each original paper was cited more than 3 times per citing paper.

Table 1: Data sources for selected reproducibility studies with the year of reproduction, the numbers of rep-studies and citation contexts for each data source.   
![](images/25020d4d0d52988ebd9cf819dcff18ae215b7b541572cfd5b8e2dd1ad96d7723.jpg)

Table 2: Distribution of original papers and citation contexts over rs_scores. The rows corresponding to zero original papers (and citation context) are not shown. Npos and Npos for models M6 and M7 are defined in Section 5.2.   
![](images/9c12b78cae4c6b342ea4d7ed79bfd8eab3792b0a1400f46c371190acd3e131ee.jpg)

# 3.4 Building the Ground Truth

As a pilot study, we randomly selected 22 original papers (Table 1) and 1937 citation contexts. We manually labeled these citation contexts into 3 reproducibility sentiments:

• positive: the context hints about reproducibility (such as re-usage about the cited paper’s data/code or the concept);   
• negative: the context hints about irreproducibility (such as unavailability of the cited paper’s data/code or unsuccessful attempts in reproducing);   
• neutral: the context simply mentions (cites) the cited paper without any hints about reproducibility.

The ground truth dataset contains 158 positive (8.1%), 23 negative (1.2%), and 1756 neutral (89.7%) citation contexts. As the distribution is skewed, we down-sampled positive and neutral citation contexts to match the number of negative citation contexts, for a balanced ground truth subset containing 69 labeled citation contexts.

# 4 Sentiment analysis

We first performed aspect-based sentiment analysis by classifying citation context into the three sentiments above. To our knowledge, there are no ready-to-use models for this task, so we trained our own ML models using the balanced ground truth subset (Section 3.4). For comparison, we selected five pre-trained open-source multiclass sentiment analysis models from HuggingFace [15] (Table 3) based on the popularity. M1-M5 were trained/fine-tuned on social media posts, tweets, or generic datasets.

We trained two in-house models using our data. The first (M6) leverages DistilBERT [22] fine-tuned using our ground truth data. Compared with BERT [23], DistilBERT is lighter, faster, and achieved the top performance for our previous reproducibility-related study [24]. Our second model is a hierarchical classifier (M7, combining M7.1 and M7.2) to verify our results obtained from M6. In the first step, we trained a binary classifier (M7.1) which classifies citation contexts as related to or not related to reproducibility. We used the full ground truth set (1937 labeled citation contexts) and merged positive and negative labels into a category called related; neutral labels were categorized as not related. In

# Can citations tell us about a paper’s reproducibility? A case study of machine learning papers

Table 3: Comparison of mean weighted average precision, recall, and F1-scores for M1-M5.   
![](images/44c25f7c502c207704a3b0ab0e9ccd6de29d7dd82aaa65c8392b0041454be57b.jpg)

Table 4: 5-fold cross-validation results for M6 and M7.   
![](images/48f271f03bbadc992a2669772d00479727ed6e42b8f492c3567890ff27b20d59.jpg)

the second step, we fine-tuned a DistilBERT binary classifier (Table 3: M7.2) to classify citation contexts labeled as related as either positive or negative.

# 5 Results

# 5.1 Sentiment Analysis

The evaluation results of the five baseline methods are shown in Table 3. These models are evaluated on the balanced ground truth subset consisting of an equal number of positive, negative, and neutral citation contexts. These baseline models were not trained on our data, which explains why they do not perform well. To evaluate M6 and M7, we performed 5-fold cross-validation (Table 4) using the ground truth set supplemented with additional positive and neutral samples. M6 and M7 achieve F1-scores of 0.70 and M7 achieved an F1-score of 0.86, respectively. We note that we were not able to test M6 and M7 on the identical data as M1-M5 because M6 and M7 incorporate some of this data for training. Nevertheless we observe M6 and M7 perform significantly better than baselines and achieve reasonably good performance.

![](images/5dcc062fe7f11a6860ee4cf9f3d0959bda05acd015e3182147c03972851e6810.jpg)  
Figure 3: Normalized citation context sentiment counts vs. reproducibility scores using M6 (left) and M7 (right).

Next, M6 and M7 were applied to all 41,244 citation contexts. Applying M6 resulted in 15,744 positive (38.17%), 2366 negative (5.74%), and 23,134 neutral (56.09%) citation contexts. Applying M7 resulted in 10,300 positive (24.97%), 1939 negative (4.70%), and 29,005 (70.33%) neutral citation contexts.

0.88 0.850 0.86 M6 0.825 0.84 0.800 0.82 0.775 0.80 0.750 0.78 0.725 0.00 0.25 0.50 0.75 1.00 0.00 0.25 0.50 0.75 1.00 0.22 0.275 M7 0.20 0.250 0.18 0.225 0.200 0.175 0.150 0.00 0.25 0.50 0.75 1.00 0.00 0.25 0.50 0.75 1.00 5 4 3 0.00 0.25 0.50 0.751.00

# 5.2 Citation Context Sentiments vs. Reproducibility Scores

Our goal is to investigate the correlation between the reproducibility sentiment of citation contexts and the reproducibility scores of original papers. Because of the strongly skewed distribution of reproducibility scores (Table 2), simply using the numbers of citation contexts will not result in meaningful conclusions. Therefore, we normalized the number of citation contexts by a factor Z = Npos + Nneg, in which Npos and Nneg are the numbers of citation contexts labeled as positive and negative reproducibility-based sentiments, respectively. Therefore, the normalized citation context counts, i.e., the fraction of positive or negative citation contexts, are given by:

Figure 3 depicts N p′ os and N n′eg using M6 and M7.

We note that N p′ os or N n′eg at certain rs_scores are calculated based on a small number of papers/contexts. For example, there is only one paper whose rs_score is 0.2 and M7 only predicts 2 positive and 4 negative citation contexts (Table 2). The low citation counts in combination with the uncertainty introduced by the sentiment classification models may lead to large uncertainties of N p′ os and N n′ eg. To obtain statistically meaningful results, we remove data points calculated based on less than 50 negative citation contexts, leaving three data points at rs_score = 0, 0.5, and 1.

Correlations between the normalized citation context count of positive or negative sentiment and the rs_scores, for M6 and M7, are shown in Figure 4. Given a cited paper, the fraction of positive citation contexts (N p′ os) increases with the reproducibility scores, and the fraction of negative citation contexts (N n′ eg) decreases with the reproducibility scores. The ratio r = N p′ /N n′eg exhibits a magnified correlation with rs_score, with r ranging from about 3.5 to 7 for M6 and

# Can citations tell us about a paper’s reproducibility? A case study of machine learning papers

from 2.5 to 5.5 for M7. Because there are only three data points for each diagram, we did not calculate the correlation and regression coefficients.

# 6 Discussion and Conclusion

In this pilot study, we explored correlations between reproducibility-based sentiments of citation context and reproducibility scores using a total of 41,244 citation contexts. We trained two sentiment analysis models and achieved F1-scores of 0.70–0.86. Both models exhibited an increasing fraction of positive sentiment citation context with rs_score and a decreasing fraction of negative sentiment citation context with rs_score. The correlation is stronger in the ratio diagrams.

If our findings are verified using larger datasets, it suggests that it is possible to statistically estimate the reproducibility of ML papers using downstream citation contexts. More precisely, our work suggests that downstream mentions of a paper contain signals about the efforts ML researchers routinely undertake to reproduce one another’s models and findings, often for purposes of extension or comparison, but which are not systematically reported as reproducibility studies. Nevertheless, this study does not imply to use of citation context sentiments to replace direct experiments to assess reproducibility. Rather, they may be useful as a surrogate to study the trends of reproducibility and its correlations with other factors for large corpora of ML papers when direct reproducibility studies are not feasible.

One limitation is the relatively low number of training data. In the future, we will extend our labeling to more papers with direct reproducibility studies, such as ML papers with ACM badges and papers with partial reproducibility scores (0 < rs_score < 1) to verify and confirm our observations. Another potential limitation is the selection bias. Most rep-studies we adopted are from MLRC, which intentionally reproduces papers published in top-tier venues. This bias can be mitigated by collecting more rep-studies based on a homogeneous selection of venues.

# References

[1] Edward Raff. A step toward quantifying independently reproducible machine learning research. In H. Wallach, H. Larochelle, A. Beygelzimer, F. d'Alché-Buc, E. Fox, and R. Garnett, editors, Advances in Neural Information Processing Systems, volume 32. Curran Associates, Inc., 2019.   
[2] Anya Belz, Shubham Agarwal, Anastasia Shimorina, and Ehud Reiter. A systematic review of reproducibility research in natural language processing. In Paola Merlo, Jorg Tiedemann, and Reut Tsarfaty, editors, Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics: Main Volume, pages 381–393, Online, April 2021. Association for Computational Linguistics.   
[3] Jian Wu, Rajal Nivargi, Sree Sai Teja Lanka, Arjun Manoj Menon, Sai Ajay Modukuri, Nishanth Nakshatri, Xin Wei, Zhuoer Wang, James Caverlee, Sarah M. Rajtmajer, and C. Lee Giles. Predicting the reproducibility of social and behavioral science papers using supervised learning models, 2021.   
[4] Y. Yang, W. Youyou, and B. Uzzi. Estimating the deep replicability of scientific findings using human and artificial intelligence. Proceedings of the National Academy of Sciences, 117:10762–10768, 2020.   
[5] Priyanshi Gupta, Yash Kumar Atri, Apurva Nagvenkar, Sourish Dasgupta, and Tanmoy Chakraborty. Inline citation classification using peripheral context and time-evolving augmentation. In Hisashi Kashima, Tsuyoshi Ide, and Wen-Chih Peng, editors, Advances in Knowledge Discovery and Data Mining, pages 3–14, Cham, 2023. Springer Nature Switzerland.   
[6] MYRIAM HERNÁNDEZ-ALVAREZ, JOSÉ M. GOMEZ SORIANO, and PATRICIO MARTÍNEZ-BARCO. Citation function, polarity and influence classification. Natural Language Engineering, 23(4):561–588, 2017.   
[7] Suchetha N. Kunnath, Drahomira Herrmannova, David Pride, and Petr Knoth. A meta-analysis of semantic classification of citations. Quantitative Science Studies, 2(4):1170–1215, 12 2021.   
[8] Sonita Te, Amira Barhoumi, Martin Lentschat, Frédérique Bordignon, Cyril Labbé, and François Portet. Citation context classification: Critical vs non-critical. In Arman Cohan, Guy Feigenblat, Dayne Freitag, Tirthankar Ghosal, Drahomira Herrmannova, Petr Knoth, Kyle Lo, Philipp Mayr, Michal Shmueli-Scheuer, Anita de Waard, and Lucy Lu Wang, editors, Proceedings of the Third Workshop on Scholarly Document Processing, pages 49–53, Gyeongju, Republic of Korea, October 2022. Association for Computational Linguistics.   
[9] Engineering National Academies of Sciences, Medicine, et al. Reproducibility and replicability in science. 2019.   
[10] ACM. , 2020. Accessed March 28, 2024.   
[11] Ambreen Nazir, Yuan Rao, Lianwei Wu, and Ling Sun. Issues and challenges of aspect-based sentiment analysis: A comprehensive survey. IEEE Transactions on Affective Computing, 13(2):845–863, 2022.   
[12] Odd Erik Gundersen and Sigbjørn Kjensmo. State of the art: Reproducibility in artificial intelligence. Proceedings of the AAAI Conference on Artificial Intelligence, 32(1), Apr. 2018.   
[13] A. Akella, D. Koop, and H. Alhoori. Laying foundations to quantify the “effort of reproducibility”. In 2023 ACM/IEEE Joint Conference on Digital Libraries (JCDL), pages 56–60, Los Alamitos, CA, USA, jun 2023. IEEE Computer Society.   
[14] Abdallah Yousif, Zhendong Niu, James Chambua, and Zahid Younas Khan. Multi-task learning model based on recurrent convolutional neural networks for citation sentiment and purpose classification. Neurocomputing, 335:195–205, 2019.   
[15] Hugging Face Team. Models - Hugging Face — huggingface.co. https://huggingface.co/models, 2024. [Accessed 05-01-2024].   
[16] Arman Cohan, Waleed Ammar, Madeleine van Zuylen, and Field Cady. Structural scaffolds for citation intent classification in scientific publications. In Jill Burstein, Christy Doran, and Thamar Solorio, editors, Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers), pages 3586–3596, Minneapolis, Minnesota, June 2019. Association for Computational Linguistics.   
[17] Indra Budi and Yaniasih Yaniasih. Understanding the meanings of citations using sentiment, role, and citation function classifications. Scientometrics, 128(1):735–759, Jan 2023.   
[18] Kehinde Ajayi, Muntabir Hasan Choudhury, Sarah M. Rajtmajer, and Jian Wu. A study on reproducibility and replicability of table structure recognition methods. In Gernot A. Fink, Rajiv Jain, Koichi Kise, and Richard Zanibbi, editors, Document Analysis and Recognition - ICDAR 2023, pages 3–19, Cham, 2023. Springer Nature Switzerland.   
[19] Rodney Michael Kinney, Chloe Anastasiades, Russell Authur, Iz Beltagy, Jonathan Bragg, Alexandra Buraczynski, Isabel Cachola, Stefan Candra, Yoganand Chandrasekhar, Arman Cohan, Miles Crawford, Doug Downey, Jason Dunkelberger, Oren Etzioni, Rob Evans, Sergey Feldman, Joseph Gorney, David W. Graham, F.Q. Hu, Regan Huff, Daniel King, Sebastian Kohlmeier, Bailey Kuehl, Michael Langan, Daniel Lin, Haokun Liu, Kyle Lo, Jaron Lochner, Kelsey MacMillan, Tyler Murray, Christopher Newell, Smita R Rao, Shaurya Rohatgi, Paul L Sayre, Zejiang Shen, Amanpreet Singh, Luca Soldaini, Shivashankar Subramanian, A. Tanaka, Alex D Wade, Linda M. Wagner, Lucy Lu Wang, Christopher Wilhelm, Caroline Wu, Jiangjiang Yang, Angele Zamarron, Madeleine van Zuylen, and Daniel S. Weld. The semantic scholar open data platform. ArXiv, abs/2301.10140, 2023.   
[20] Koustuv Sinha. ML Reproducibility Challenge 2023 | MLRC2023 — reproml.org. https://reproml.org/, 2023. [Accessed 03-02-2024].   
[21] RESCIENCE C. ReScience C — rescience.github.io. https://rescience.github.io/read/, 2023. [Accessed 10-02-2024].   
[22] Victor Sanh, Lysandre Debut, Julien Chaumond, and Thomas Wolf. Distilbert, a distilled version of BERT: smaller, faster, cheaper and lighter. CoRR, abs/1910.01108, 2019.   
[23] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. BERT: Pre-training of deep bidirectional transformers for language understanding. In Jill Burstein, Christy Doran, and Thamar Solorio, editors, Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers), pages 4171–4186, Minneapolis, Minnesota, June 2019. Association for Computational Linguistics.   
[24] Lamia Salsabil, Jian Wu, Muntabir Hasan Choudhury, William A. Ingram, Edward A. Fox, Sarah M. Rajtmajer, and C. Lee Giles. A study of computational reproducibility using urls linking to open access datasets and software. In Companion Proceedings of the Web Conference 2022, WWW ’22, page 784–788, New York, NY, USA, 2022. Association for Computing Machinery.   
[25] Jochen Hartmann, Mark Heitmann, Christina Schamp, and Oded Netzer. The power of brand selfies. Journal of Marketing Research, 2021.   
[26] Seethal. Seethal/sentiment-analysis-generic-dataset · Hugging Face — huggingface.co. https://huggingface. co/Seethal/sentiment_analysis_generic_dataset, 2022. [Accessed 10-02-2024].   
[27] Juan Manuel Pérez, Juan Carlos Giudici, and Franco Luque. pysentimiento: A python toolkit for sentiment analysis and socialnlp tasks, 2021.   
[28] Souvick Das. Souvikcmsa/BERT-sentiment-analysis Hugging Face — huggingface.co. https://huggingface. co/Souvikcmsa/BERT_sentiment_analysis, 2022. [Accessed 10-02-2024].   
[29] BI team. sbcBI/sentiment-analysis-model · Hugging Face — huggingface.co. https://huggingface.co/ sbcBI/sentiment_analysis_model, 2022. [Accessed 10-02-2024].