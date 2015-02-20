#!/bin/python3

import irc.bot
import json

# Local imports

def load_config(filename):
    text = ''
    with open(filename, 'r') as config_file:
        text = config_file.read();
    return json.loads(text)



class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, config):
        self.config_filename = config
        self.config = load_config(config)
        super().__init__(
                [(self.config['server'].split(':')[0], int(self.config['server'].split(':')[1]))],
                    self.config['nick'], self.config['realname'])
        self.connection.buffer_class = irc.buffer.LenientDecodingLineBuffer


    def update_user_modes(self, channel_name, nick, user, host):
        channel = self.channels[channel_name]
        fullname = "%s@%s"%(user, host)

        if fullname in self.config['channels'][channel_name]['ops']:
            print(fullname, 'is op')
            self.connection.mode(channel_name, "+o %s"%nick)

        if fullname in self.config['channels'][channel_name]['voice']:
            print(fullname, 'is voice')
            self.connection.mode(channel_name, "+v %s"%nick)


    def on_welcome(self, connection, event):
        print("connected!")
        for channel in self.config['channels'].keys():
            connection.join(channel)


    def on_join(self, connection, event):
        print(vars(event))
        nick = event.source.split("!")[0]
        if nick == self.config['nick']:
            print("joined ", event.target)

            # If we're somehow already an operator, trigger mode set by WHO
            if self.channels[event.target].is_oper(nick):
                connection.who(event.target)
                print("users: ", self.channels[event.target].users())

        else:
            print(event.source, " joined ", event.target)
            connection.who(nick)

    
    def on_mode(self, connection, event):
        if event.arguments[1] == self.config['nick'] and event.arguments[0] == "+o":
            connection.who(event.target)


    def on_namreply(self, connection, event):
        print(event.arguments)


    def on_whoreply(self, conn, event):
        print(event.arguments)
        print("user: ", self.channels[event.arguments[0]].users())
        self.update_user_modes(event.arguments[0], event.arguments[1], event.arguments[4], event.arguments[2])


    #def on_privmsg(self, conn, event):
    #    print(vars(event))
    #    parse_command

    def on_pubmsg(self, conn, event):
        print(vars(event))
        msg = event.arguments[0].strip()

        if msg[:len(self.config['nick'])+2] == "%s: "%self.config['nick']:
            print(event.source, " commanded '%s'"%msg[len(self.config['nick'])+2:])
            self.parse_command(event.source, event.target, msg[len(self.config['nick'])+2:].strip())


    def parse_command(self, issuer, channel, command):
        if issuer.split("!")[1] in self.config['admins']:
            if command == "reload":
                try:
                    self.reload()
                    self.connection.privmsg(channel, "%s: yes, sir!"%issuer.split("!")[0])
                except ValueError:
                    self.connection.privmsg(channel, "%s: error in configuration"%issuer.split("!")[0])
            else:
                self.connection.privmsg(channel, "%s: unknown command"%issuer.split("!")[0])
        else:
            self.connection.privmsg(channel, "%s: permission denied"%issuer.split("!")[0])
            

    def reload(self):
        self.config = load_config(self.config_filename)
        for channel_name in self.channels.keys():
            if self.channels[channel_name].is_oper(self.config['nick']):
                self.connection.who(channel_name)



def main():
    #bot.on_welcome = on_connect
    #bot.on_join = on_join
    anna = Bot('config.json')
    
    anna.start()


if __name__ == '__main__':
    main()

