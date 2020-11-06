import cv2 as cv
import flask
import webbrowser


def main():
    app = flask.Flask("Kamera HTML")

    @app.route('/')
    def html_camera():
        return flask.render_template("index.html")

    capture = cv.VideoCapture(0)  # 0 = pierwsze urządzenie
    # sprawdzenie czy kamera jest dobrze 'otwarta'
    if not capture.isOpened():
        raise IOError("Nie można otworzyć kamery")

    width, height = 1280, 720
    capture.set(cv.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, height)

    title = "Kamera"
    cv.namedWindow(title)

    alpha, beta = 1.0, 0
    recording = False
    recorder = cv.VideoWriter("Film.avi", 0, 20, (width, height))
    detecting_motion = False
    prev_frame = None

    while capture.isOpened():
        # pobranie obrazu z kamery
        reading, frame = capture.read()
        # zmiana rozdzielczości obrazu
        frame = cv.resize(frame, None, fx=width / 1280, fy=height / 720, interpolation=cv.INTER_AREA)
        # zmiana kontrastu i jasności obrazu
        frame = cv.convertScaleAbs(frame, alpha=alpha, beta=beta)

        if recording:
            recorder.write(frame)

        cv.putText(frame, f"Alpha={format(alpha, '.1f')}, Beta={format(beta, '.1f')}", (0, 24), cv.FONT_HERSHEY_SIMPLEX,
                   1, (255, 255, 255))

        # wyświetlenie obrazu
        cv.imshow(title, frame)

        if detecting_motion:
            if prev_frame is not None:
                #  skala szarości, 3 razy mniej obliczeń
                prev_frame = cv.cvtColor(prev_frame, cv.COLOR_BGR2GRAY)
                frame_copy = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

                # rozmycie, pozbycie się ostrych krawędzi
                prev_frame = cv.GaussianBlur(prev_frame, (21, 21), 0)
                frame_copy = cv.GaussianBlur(frame_copy, (21, 21), 0)

                # różnica między klatkami
                delta_frame = cv.absdiff(prev_frame, frame_copy)

                # zaznaczenie pikseli, które różnią się od poprzedniej klatki o threshold
                thresh_frame = cv.threshold(delta_frame, 5, 255, cv.THRESH_BINARY)[1]
                cv.dilate(thresh_frame, None, iterations=2)

                # wyznaczenie prostokątnych konturów z różnic
                contours, _ = cv.findContours(thresh_frame, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

                # wyznaczenie czy prostokątny kontur był wystarczająco duży, aby uznać go za ruch
                rectangles = []
                for c in contours:
                    if cv.contourArea(c) < 1 / 750 * width * height:
                        continue
                    rectangles.append(cv.boundingRect(c))

                # zaznaczenie na klatce wszystkich miejsc gdzie wykryto ruch
                frame_copy = frame.copy()
                for rect in rectangles:
                    x = rect[0]
                    y = rect[1]
                    w = rect[2]
                    h = rect[3]
                    cv.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 0, 255), 5)
                cv.imshow("Detektor ruchu", frame_copy)

        # obecna klatka w następnej iteracji będzie poprzednią klatką
        prev_frame = frame

        c = cv.waitKey(1)
        if c == 27:  # Esc
            break
        elif c == 65 or c == 97:  # A/a
            alpha += 0.2
        elif c == 90 or c == 122:  # Z/z
            alpha -= 0.2
        elif c == 83 or c == 115:  # S/s
            beta += 5
        elif c == 88 or c == 120:  # X/x
            beta -= 5
        elif c == 32:  # Spacja
            filename = input("Podaj nazwę pliku (nazwa musi zawierać rozszerzenie): ")
            cv.imwrite(filename, frame)
        elif c == 82 or c == 114:  # R/r
            if not recording:
                recording = True
            else:
                recorder.release()
        elif c == 67 or c == 99:  # C/c
            try:
                width = int(input("Podaj szerokość: "))
                height = int(input("Podaj wysokość: "))
            except Exception as e:
                print(e)
        elif c == 77 or c == 109:  # M/m
            if not detecting_motion:
                detecting_motion = True
            else:
                detecting_motion = False
        elif c == 87 or c == 119:  # W/w
            capture.release()
            webbrowser.open("http://127.0.0.1:5000/", new=1)
            app.run()

    capture.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
