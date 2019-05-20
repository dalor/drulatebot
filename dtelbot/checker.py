from threading import Thread

class Checker(Thread):
  def __init__(self, bot, result):
    Thread.__init__(self)
    self.bot = bot
    self.result = result
    self.oop = bot.oop
  
  def get_by_path(self, dict, path):
    for p in path:
      if not dict:
        break
      dict = dict.get(p)
    return dict
  
  def run(self):
    for mess_type, mess in self.result.items():
      commands = self.bot.commands.get(mess_type)
      if commands:
        for command in commands:
          if command:
            matcher = command['match']
            text = self.get_by_path(mess, command['path'])
            match = None
            if matcher is True or matcher == text:
              match = text
            elif type(text) == str:
              match = command['match'].match(text)
            if match:
              _a_ = command['return'](mess_type, mess, match, self.bot)
              if self.oop:
                command['run'](self, _a_)
              else:
                command['run'](_a_)
              user_session = _a_._session
              if user_session:
                user_session.update_in_db()
              return

  