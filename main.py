import cv2
import csv
import io
import cvzone
import time
import math
import streamlit as st
from cvzone.HandTrackingModule import HandDetector

class Question:
    def __init__(self, data):
        self.question = data[0]
        self.choice1 = data[1]
        self.choice2 = data[2]
        self.choice3 = data[3]
        self.choice4 = data[4]
        self.answer = int(data[5])
        self.userAnswer = None

    def update(self, cursor, bboxs, img):
        for x, bbox in enumerate(bboxs):
            x1, y1, x2, y2 = bbox
            if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                self.userAnswer = x + 1
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), cv2.FILLED)


def findDistance(p1, p2):
    x1, y1, _ = p1[:3]
    x2, y2, _ = p2[:3]
    length = math.hypot(x2 - x1, y2 - y1)
    return length, [x1, y1, x2, y2]


def main():
    # Titre de l'application
    st.title('Application de Quiz Virtuel')

    # Description de l'application
    st.markdown(
        'Cette application vous permet de participer à un Quiz virtuel interactif à l\'aide de la détection de main. '
        'Vous pouvez importer un fichier CSV contenant les questions et les réponses possibles du Quiz. '
        'Lorsque vous êtes prêt, vous pouvez utiliser vos mains pour sélectionner les réponses et avancer dans le Quiz.'
        ' À la fin du Quiz, vous obtiendrez votre score.')

    # Description du format du fichier CSV
    st.markdown('## fichier CSV')
    st.markdown('''
                    - La première colonne doit contenir les questions du Quiz.
                    - Les quatre colonnes suivantes doivent contenir les réponses possibles, chaque réponse dans une colonne distincte.
                    - La dernière colonne doit contenir le numéro de la réponse correcte (1, 2, 3 ou 4).
                    - Assurez-vous que le fichier CSV ne contient pas de lignes d'en-tête supplémentaires, à l'exception de la première ligne avec les noms de colonnes.

                    Exemple de format de fichier CSV :

                    | Question                               | Réponse 1    | Réponse 2    | Réponse 3    | Réponse 4    | Réponse Correcte |
                    |----------------------------------------|--------------|--------------|--------------|--------------|------------------|
                    | Quelle est la capitale de la France ?    | Paris        | Londres      | Rome         | Madrid       | 1                |
                    | Quel est le symbole chimique de l'or ?  | Au           | Ag           | Fe           | Hg           | 1                |
                    | Quelle est la couleur du ciel ?         | Bleu         | Vert         | Rouge        | Jaune        | 1                |
                    ''')

    # Titre de la barre latérale
    st.sidebar.title('Entrée des données')

    # Titre de la sortie
    st.markdown('## Résultat')
    stframe = st.empty()

    # Initialisation du détecteur de main
    detector = HandDetector(detectionCon=0.8, maxHands=2)
    cap = cv2.VideoCapture(0)

    cap.set(3, 1280)
    cap.set(4, 720)

    # Importer les données du fichier CSV
    st.sidebar.title('Importer un fichier CSV')

    # Uploader le fichier CSV
    csv_file = st.sidebar.file_uploader('Importer un fichier CSV', type=['csv'])

    # Vérifier si un fichier est importé
    if csv_file is not None:
        # Lire le fichier CSV
        csv_data = io.TextIOWrapper(csv_file, encoding='utf-8')
        dataAll = list(csv.reader(csv_data))[1:]

        # Créer un objet pour chaque question du QCM
        mcqList = [Question(q) for q in dataAll]
        qTotal = len(dataAll)

        qNo = 0
        play_again = False

        # Créer une barre de progression
        progress_bar = st.progress(0)

        while True:
            if play_again:
                qNo = 0
                play_again = False

            success, img = cap.read()

            if not success:
                break
            img = cv2.flip(img, 1)
            hands, img = detector.findHands(img, flipType=False)

            if qNo < qTotal:
                mcq = mcqList[qNo]

                img, bbox1 = cvzone.putTextRect(img, mcq.question, [100, 100], 2, 2, offset=50, border=5)
                img, bbox2 = cvzone.putTextRect(img, mcq.choice1, [100, 250], 2, 2, offset=50, border=5)
                img, bbox3 = cvzone.putTextRect(img, mcq.choice2, [400, 250], 2, 2, offset=50, border=5)
                img, bbox4 = cvzone.putTextRect(img, mcq.choice3, [100, 400], 2, 2, offset=50, border=5)
                img, bbox5 = cvzone.putTextRect(img, mcq.choice4, [400, 400], 2, 2, offset=50, border=5)

                if hands:
                    lmList = hands[0]['lmList']
                    cursor = lmList[8]
                    length, _ = findDistance(lmList[8], lmList[12])

                    if length < 35:
                        mcq.update(cursor, [bbox1, bbox2, bbox3, bbox4, bbox5], img)
                        if mcq.userAnswer is not None:
                            time.sleep(0.3)
                            qNo += 1

            else:
                score = sum(1 for mcq in mcqList if mcq.answer == mcq.userAnswer)
                score = round((score / qTotal) * 100, 2)
                img, _ = cvzone.putTextRect(img, "Quiz Terminé", [215, 200], 2, 2, offset=50, border=5)
                img, _ = cvzone.putTextRect(img, f'Votre score : {score}%', [750, 200], 2, 2, offset=50, border=5)

                # Bouton "Jouer à nouveau"
                img, bboxf = cvzone.putTextRect(img, f'Jouer à nouveau', [525, 500], 2, 2, offset=50, border=5)
                if hands:
                    lmList = hands[0]['lmList']
                    cursor = lmList[8]
                    length, _ = findDistance(lmList[8], lmList[12])

                    if length < 35:
                        x1, y1, x2, y2 = bboxf

                        if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), cv2.FILLED)
                            play_again = True

            # Dessiner la barre de progression
            progress_percentage = round(qNo / qTotal, 2)
            progress_bar.progress(progress_percentage)

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            stframe.image(img, use_column_width=True)

            if cv2.waitKey(1) == ord('q'):
                break

    else:
        st.sidebar.write('Veuillez importer un fichier CSV.')

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
