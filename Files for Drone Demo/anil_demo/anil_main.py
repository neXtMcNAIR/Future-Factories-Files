import anil_tello
import anil_ui

def main():

    drone = anil_tello.Tello('', 8889)

    vplayer = anil_ui.TelloUI(drone)
    vplayer.root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        raise e
