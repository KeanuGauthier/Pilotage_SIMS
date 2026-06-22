\section{Contraintes d’accès entre Jenkins, la production et l’environnement de test}
\label{annexe:contraintes-acces-jenkins}

Cette annexe est associée à la partie 4.5, relative aux difficultés rencontrées et aux choix d’adaptation. Elle présente la contrainte d’accès identifiée lors de l’intégration des tests automatisés dans Jenkins.

\begin{table}[H]
\centering
\renewcommand{\arraystretch}{1.35}

\begin{tabularx}{\textwidth}{
    >{\raggedright\arraybackslash}p{0.24\textwidth}
    >{\raggedright\arraybackslash}p{0.23\textwidth}
    >{\raggedright\arraybackslash}p{0.23\textwidth}
    >{\raggedright\arraybackslash}X
}
\toprule
\textbf{Élément concerné} 
& \textbf{Accès à la production} 
& \textbf{Accès à l’environnement de test} 
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
Jenkins peut transmettre les résultats vers la production, notamment via API. En revanche, l’accès direct aux pages de l’environnement de test est limité par les règles réseau. \\

\midrule

Adaptation nécessaire
&
\textcolor{green!45!black}{Conservé}
&
\textcolor{blue!70!black}{À ouvrir de manière ciblée}
&
Une autorisation spécifique est nécessaire pour permettre à la machine virtuelle Jenkins d’exécuter les tests sur l’environnement de test. \\

\bottomrule
\end{tabularx}

\caption{Synthèse des accès possibles et bloqués entre les environnements.}
\label{tab:contraintes-acces-jenkins}
\end{table}

\begin{figure}[H]
\centering

\resizebox{\textwidth}{!}{%
\begin{tikzpicture}[
    box/.style args={#1}{
        rectangle,
        rounded corners=3mm,
        draw=#1!65!black,
        fill=#1!10,
        very thick,
        align=center,
        text width=4.1cm,
        minimum height=1.65cm,
        font=\small
    },
    smallbox/.style args={#1}{
        rectangle,
        rounded corners=3mm,
        draw=#1!60!black,
        fill=#1!8,
        thick,
        align=center,
        text width=3.5cm,
        minimum height=1.25cm,
        font=\small
    },
    lbl/.style={
        font=\small\bfseries,
        fill=white,
        inner sep=2pt,
        align=center
    },
    ok/.style={
        -{Latex[length=3mm]},
        draw=green!45!black,
        very thick
    },
    blocked/.style={
        -{Latex[length=3mm]},
        draw=red!70!black,
        very thick,
        dashed
    },
    request/.style={
        -{Latex[length=3mm]},
        draw=blue!70!black,
        very thick,
        dotted
    },
    note/.style={
        rectangle,
        rounded corners=3mm,
        draw=black!45,
        fill=gray!5,
        align=left,
        text width=14.5cm,
        inner sep=0.35cm,
        font=\small
    }
]

% =========================
% Schéma principal : Jenkins
% =========================

\node[box=orange] (jenkins) at (0,0) {
    \textbf{Jenkins}\\[0.1cm]
    Scripts Python/Selenium\\
    Hébergé côté production
};

\node[box=green] (prod) at (8.2,2.25) {
    \textbf{Production}\\[0.1cm]
    Zephyr, rapports et API\\
    Environnement principal
};

\node[box=purple] (test) at (8.2,-2.25) {
    \textbf{Environnement de test}\\[0.1cm]
    Serveur de pré-production\\
    Pages Jira/Confluence à vérifier
};

% Jenkins vers production : possible
\draw[ok]
    (jenkins.east) --
    node[lbl, above, sloped, yshift=1mm] {API résultats\\possible}
    (prod.west);

% Jenkins vers environnement de test : bloqué
\draw[blocked]
    (jenkins.east) --
    node[lbl, below, sloped, yshift=-1mm] {Accès direct\\actuellement bloqué}
    (test.west);

\node[
    font=\bfseries\Large,
    text=red!70!black,
    fill=white,
    inner sep=1pt
] at ($(jenkins.east)!0.55!(test.west)$) {$\times$};

% Accès à ouvrir : Jenkins vers environnement de test
\draw[request]
    ($(jenkins.south east)+(0.05,-0.15)$)
    .. controls (2.8,-3.85) and (5.2,-3.85) ..
    node[lbl, below, pos=0.52] {Ouverture réseau ciblée à demander}
    ($(test.south west)+(-0.05,-0.15)$);

% =========================
% Comparaison : poste utilisateur
% =========================

\node[smallbox=gray] (user) at (0,-5.4) {
    \textbf{Poste utilisateur autorisé}\\
    Accès via navigateur
};

\node[smallbox=green] (userprod) at (4.4,-5.4) {
    \textbf{Production}\\
    Accès possible
};

\node[smallbox=purple] (usertest) at (8.2,-5.4) {
    \textbf{Environnement de test}\\
    Accès possible
};

\draw[ok]
    (user.east) --
    node[lbl, above] {possible}
    (userprod.west);

\draw[ok]
    (userprod.east) --
    node[lbl, above] {possible}
    (usertest.west);

% =========================
% Note explicative
% =========================

\node[note] at (4.1,-7.55) {
    \textbf{Lecture du schéma}\\[0.15cm]
    Le poste utilisateur autorisé peut accéder aux environnements de production et de test. 
    La contrainte concerne Jenkins : l’outil étant hébergé côté production, il peut transmettre les résultats vers la production via API, mais ne dispose pas actuellement d’un accès direct aux pages de l’environnement de test. 
    Une ouverture réseau ciblée est donc nécessaire pour permettre l’exécution complète des tests automatisés.
};

\end{tikzpicture}
}

\caption{Contraintes d’accès entre Jenkins, la production et l’environnement de test.}
\label{fig:contraintes-acces-jenkins}

\end{figure}

\noindent
Cette contrainte explique pourquoi l’intégration complète des tests automatisés nécessite une adaptation de l’architecture d’accès. L’enjeu n’est pas lié au fonctionnement des scripts eux-mêmes, mais à la capacité de Jenkins à atteindre l’environnement de test tout en conservant la transmission des résultats vers l’environnement de production.