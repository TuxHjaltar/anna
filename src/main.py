#!/bin/python3

import irc.bot
import json
import wolframalpha
import re

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

        self.wa_client = None
        if "wa_appid" in self.config:
            self.wa_client = wolframalpha.Client(self.config["wa_appid"])


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
        if event.arguments[0] not in self.channels:
            return
        print("user: ", self.channels[event.arguments[0]].users())
        self.update_user_modes(event.arguments[0], event.arguments[1], event.arguments[4], event.arguments[2])


    #def on_privmsg(self, conn, event):
    #    print(vars(event))
    #    parse_command

    def on_pubmsg(self, conn, event):
        print(vars(event))
        msg = event.arguments[0].strip()
        match = re.match('%s(,|:)\s+(.+)'%self.config['nick'], msg)
        command = None
        if match:
            command = match.groups()[1]
        else:
            return

        print(event.source, " commanded '%s'"%command)
        self.parse_command(event.source, event.target, command)


    def parse_command(self, issuer, channel, command):
        issuer_nick = issuer.split("!")[0]
        issuer_ident = issuer.split("!")[1]
        if issuer_ident in self.config['admins']:
            if command == "reload":
                try:
                    self.reload()
                    self.connection.privmsg(channel, "%s: yes, sir!"%issuer_nick)
                except ValueError:
                    self.connection.privmsg(channel, "%s: error in configuration"%issuer_nick)
                return

        if self.attempt_wa_query(channel, issuer_nick, command):
            return
        else:
            self.connection.privmsg(channel, "%s: unknown command"%issuer_nick)
            

    def reload(self):
        self.config = load_config(self.config_filename)

        if "wa_appid" in self.config:
            self.wa_client = wolframalpha.Client(self.config["wa_appid"])

        for channel_name in self.channels.keys():
            if self.channels[channel_name].is_oper(self.config['nick']):
                self.connection.who(channel_name)

    def attempt_wa_query(self, channel, issuer, command):
        match = re.match("^what is (.+?)\\?+$", command)
        if match:
            self.wa_query(channel, issuer, match.groups()[0])
            return True
        else:
            return False


    def wa_query(self, channel, issuer, query):
        if self.wa_client:
            result = None
            try:
                result = self.wa_client.query(query)
            except:
                # try again
                try:
                    result = self.wa_client.query(query)
                except:
                    self.connection.privmsg(channel, "%s: knowledge unavailable at this time"%issuer)
                    return

            if result != None:
                for pod in result.pods:
                    if pod.title == "Result" or pod.title == "Current result":
                        self.connection.privmsg(channel, "%s: %s"%(issuer, pod.text.split('\n')[0]))
                        #replace('\n', ' ')))
                        return

                self.connection.privmsg(channel, "%s: I don't know"%issuer)
        else:
            self.connection.privmsg(channel, "%s: knowledge unavailable"%issuer)


def main():
    #bot.on_welcome = on_connect
    #bot.on_join = on_join
    anna = Bot('config.json')
    
    anna.start()


if __name__ == '__main__':
    main()

