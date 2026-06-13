from gui.splash import SplashScreen
from gui.app import App


def main() -> None:
    SplashScreen().run()
    App().run()


if __name__ == "__main__":
    main()
