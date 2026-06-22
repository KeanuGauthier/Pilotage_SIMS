\section{Contraintes d’accès entre Jenkins, la production et l’environnement de test}
\label{annexe:contraintes-acces-jenkins}

Cette annexe est associée à la partie 4.5, relative aux difficultés rencontrées et aux choix d’adaptation. Elle présente la contrainte d’accès identifiée lors de l’intégration des tests automatisés dans Jenkins.

\begin{table}[H]
\centering
\renewcommand{\arraystretch}{1.35}
\small

\begin{tabularx}{\textwidth}{
    >{\raggedright\arraybackslash}p{0.25\textwidth}
    >{\centering\arraybackslash}p{0.19\textwidth}
    >{\centering\arraybackslash}p{0.22\textwidth}
    >{\raggedright\arraybackslash}X
}
\toprule
\textbf{Élément concerné} 
& \textbf{Production} 
& \textbf{Environnement de test} 
& \textbf{Commentaire} \\
\midrule

Poste utilisateur autorisé
&
\textcolor{green!45!black}{Possible}
&
\textcolor{green!45!black}{Possible}
&
Un poste utilisateur disposant des droits nécessaires peut accéder aux deux environnements depuis un navigateur. \\

\midrule

Jenkins hébergé côté production
&
\textcolor{green!45!black}{Possible}
&
\textcolor{red!70!black}{Bloqué actuellement}
&
Jenkins peut transmettre les résultats vers la production via API. En revanche, il ne peut pas accéder directement aux pages de l’environnement de test. \\

\midrule

Adaptation nécessaire
&
\textcolor{green!45!black}{Conservé}
&
\textcolor{blue!70!black}{À ouvrir de manière ciblée}
&
Une autorisation réseau spécifique est nécessaire pour permettre à Jenkins d’exécuter les tests sur l’environnement de test. \\

\bottomrule
\end{tabularx}

\caption{Synthèse des accès possibles et bloqués entre les environnements.}
\label{tab:contraintes-acces-jenkins}
\end{table}

\begin{figure}[H]
\centering

\begin{tikzpicture}[
    bloc/.style args={#1}{
        rectangle,
        rounded corners=2.5mm,
        draw=#1!65!black,
        fill=#1!9,
        very thick,
        align=center,
        text width=4.15cm,
        minimum height=1.18cm,
        inner sep=5pt,
        font=\footnotesize
    },
    titre/.style={
        font=\bfseries\small,
        anchor=west,
        text=black!85
    },
    lbl/.style={
        font=\scriptsize\bfseries,
        fill=white,
        inner sep=2pt,
        align=center
    },
    ok/.style={
        -{Latex[length=2.7mm]},
        draw=green!45!black,
        line width=1.1pt
    },
    blocked/.style={
        -{Latex[length=2.7mm]},
        draw=red!70!black,
        line width=1.1pt,
        dashed
    },
    request/.style={
        -{Latex[length=2.7mm]},
        draw=blue!70!black,
        line width=1.2pt,
        dotted
    },
    legend/.style={
        font=\scriptsize,
        anchor=west
    }
]

% ==================================================
% A. Cas d’un poste utilisateur autorisé
% ==================================================

\node[titre] at (-0.15,1.75) {A. Accès depuis un poste utilisateur autorisé};

\node[bloc=gray] (user) at (2.05,0) {
    \textbf{Poste utilisateur}\\[0.06cm]
    Accès via navigateur\\
    avec droits adaptés
};

\node[bloc=green] (prodA) at (11.25,0.95) {
    \textbf{Production}\\[0.06cm]
    Zephyr, rapports et API
};

\node[bloc=purple] (testA) at (11.25,-1.35) {
    \textbf{Environnement de test}\\[0.06cm]
    Pré-production et pages à vérifier
};

\draw[ok]
    (user.east) .. controls (5.0,0.55) and (7.8,0.95) ..
    node[lbl, above, pos=0.56] {accès possible}
    (prodA.west);

\draw[ok]
    (user.east) .. controls (5.0,-0.55) and (7.8,-1.35) ..
    node[lbl, below, pos=0.56] {accès possible}
    (testA.west);

% ==================================================
% B. Cas Jenkins
% ==================================================

\begin{scope}[yshift=-4.25cm]

\node[titre] at (-0.15,1.75) {B. Accès depuis Jenkins hébergé côté production};

\node[bloc=orange] (jenkins) at (2.05,0) {
    \textbf{Jenkins}\\[0.06cm]
    Exécution des scripts Python/Selenium\\
    hébergée côté production
};

\node[bloc=green] (prodB) at (11.25,0.95) {
    \textbf{Production}\\[0.06cm]
    Zephyr, rapports et API
};

\node[bloc=purple] (testB) at (11.25,-1.35) {
    \textbf{Environnement de test}\\[0.06cm]
    Pré-production et pages à vérifier
};

\draw[ok]
    (jenkins.east) .. controls (5.1,0.58) and (7.8,0.95) ..
    node[lbl, above, pos=0.55] {API résultats possible}
    (prodB.west);

\draw[blocked]
    (jenkins.east) .. controls (5.1,-0.42) and (7.8,-1.35) ..
    node[lbl, above, pos=0.55] {accès direct bloqué}
    (testB.west);

\draw[request]
    ($(jenkins.south east)+(0,-0.15)$)
    .. controls (5.1,-2.45) and (7.8,-2.45) ..
    node[lbl, below, pos=0.55] {ouverture réseau ciblée à demander}
    ($(testB.south west)+(0,-0.15)$);

\end{scope}

% ==================================================
% Légende visuelle
% ==================================================

\draw[ok] (0.1,-7.65) -- (1.15,-7.65);
\node[legend] at (1.3,-7.65) {Accès possible};

\draw[blocked] (4.15,-7.65) -- (5.20,-7.65);
\node[legend] at (5.35,-7.65) {Accès actuellement bloqué};

\draw[request] (8.65,-7.65) -- (9.70,-7.65);
\node[legend] at (9.85,-7.65) {Accès à ouvrir};

\end{tikzpicture}

\caption{Contraintes d’accès entre Jenkins, la production et l’environnement de test.}
\label{fig:contraintes-acces-jenkins}

\end{figure}

\noindent
\textbf{Lecture du schéma.} Un poste utilisateur autorisé peut accéder aux environnements de production et de test. La contrainte concerne Jenkins : l’outil peut transmettre les résultats vers la production via API, mais l’accès direct aux pages de l’environnement de test est actuellement bloqué par les règles réseau. Une ouverture ciblée est donc nécessaire pour exécuter les tests automatisés sur l’environnement de test tout en conservant la remontée des résultats vers la production.

\medskip

\noindent
Cette contrainte explique pourquoi l’intégration complète des tests automatisés nécessite une adaptation de l’architecture d’accès. L’enjeu n’est pas lié au fonctionnement des scripts eux-mêmes, mais à la capacité de Jenkins à atteindre l’environnement de test tout en conservant la transmission des résultats vers l’environnement de production.