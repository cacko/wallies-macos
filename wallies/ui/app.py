from traceback import print_exc
import rumps
from ..core.scheduler import Scheduler
from wallies.core.thread import StoppableThread
from wallies.core.manager import Manager
from .menu.interval import IntervalList, Option
from wallies.ui.models import INTERVAL_OPTIONS, ActionItem, Icon, Label
from wallies.core.models import Command

class WalliesAppMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    def quit(cls):
        cls().terminate()


class WalliesApp(rumps.App, metaclass=WalliesAppMeta):

    manager: Manager = None
    __threads = []
    __intervals: IntervalList = None

    def __init__(self):
        super(WalliesApp, self).__init__(
            name="Wallies",
            menu=[
                ActionItem.random,
                ActionItem.interval,
                None,
                ActionItem.quit
            ],
            icon=Icon.APP.value,
            quit_button=None,
            template=True
        )
        self.menu.setAutoenablesItems = False
        self.__intervals = IntervalList(self, Label.INTERVAL.value)
        self.manager = Manager()
        t = StoppableThread(target=self.manager.start, args=[self.onManagerResult])
        t.start()
        self.__threads.append(t)
        self.__threads.append(Scheduler.start(self.manager))
        self.__intervals.update(
            [Option(text=t,value=v,icon=i) for v,t,i in INTERVAL_OPTIONS],
            self.onIntervalItem
        )
    
    @property
    def threads(self):
        return self.__threads


    @rumps.clicked(Label.RANDOM.value)
    def onRandom(self, sender):
        self.manager.commander.put_nowait((Command.RANDOM, None))

    def onIntervalItem(self, sender):
        print(sender)

    @rumps.clicked(Label.QUIT.value)
    def onQuit(self, sender):
        self.terminate()

    @rumps.events.on_screen_sleep
    def sleep(self):
        pass

    @rumps.events.on_screen_wake
    def wake(self):
        pass

    def onManagerResult(self, resp):
        method = f"_on{resp.__class__.__name__}"
        if hasattr(self, method):
            getattr(self, method)(resp)

    @rumps.events.before_quit
    def terminate(self):
        self.manager.commander.put_nowait((Command.QUIT, None))
        for th in self.__threads:
            try:
                th.stop()
            except Exception as e:
                pass
        try:
            rumps.quit_application()
        except Exception as e:
            print_exc(e)
