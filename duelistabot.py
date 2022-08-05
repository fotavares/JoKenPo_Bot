# -*- coding: utf-8 -*-

import random
import json
import emoji
import re
import os
from dotenv import load_dotenv
from telegram import Update,Chat,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext,CallbackQueryHandler,ContextTypes

PATH = os.path.dirname(os.path.abspath(__file__))
JSON_JOGOS = os.path.join(PATH,  "jogos.json")

load_dotenv()

TOKEN = os.getenv('TOKEN')


class json_jogos:
	js = None
	def __init__(self):
		with open(JSON_JOGOS, "r", encoding = "utf-8") as jsfile:
			self.js = json.load(jsfile)

	def insert_or_update(self,chat,mensagem,p1 = None,p2 = None,voto1 = None,voto2 = None):
		found = False
		for j in self.js['jogos']:
			if 'chat_id' not in j:
				break

			if j['chat_id'] == chat and j["msg_id"] == mensagem:
				found = True
				if p1:
					j["voto1"] = voto1
				if p2:
					j["voto2"] = voto2

		if not found:
			newjs = {"chat_id":chat,"msg_id":mensagem,"player1":p1,"player2":p2,"voto1":voto1,"voto2":voto2}
			self.js['jogos'].append(newjs)
		self.save()

	def get(self,chat,mensagem):
		for j in self.js['jogos']:
			if j['chat_id'] == chat and j["msg_id"] == mensagem:
				return j

	def remove(self,chat,mensagem):
		self.js

	def save(self):
		with open(JSON_JOGOS, 'w', encoding='utf-8') as f:
			json.dump(self.js, f, ensure_ascii=False, indent=4)


emojis = {
	"0":emoji.emojize(":punch:",language='alias'),
	"1":emoji.emojize(":v:",language='alias'),
	"2":emoji.emojize(":raised_hand:",language='alias')
	}

def get_result(partida):
	v1 = partida['voto1']
	v2 = partida['voto2']

	if v1 == "0": #pedra
		if v2 == "0":
			return None
		elif v2 == "1":
			return partida['player1']
		elif v2 == "2":
			return partida['player2']
	elif v1 == "1": #tesoura
		if v2 == "0":
			return partida['player2']
		elif v2 == "1":
			return None
		elif v2 == "2":
			return partida['player1']
	elif v1 == "2": #papel
		if v2 == "0":
			return partida['player2']
		elif v2 == "1":
			return partida['player1']
		elif v2 == "2":
			return None

def formata_botoes_telegram():
	teclado_full = []
	opcao = []
	global emojis

	opcao.append(InlineKeyboardButton(text=emojis["0"], callback_data="0"))
	opcao.append(InlineKeyboardButton(text=emojis["1"], callback_data="1"))
	opcao.append(InlineKeyboardButton(text=emojis["2"], callback_data="2"))
	teclado_full.append(opcao)
	
	keybVoto = InlineKeyboardMarkup(inline_keyboard=teclado_full)

	return keybVoto

def trata_comandos(update: Update, context: CallbackContext) -> None:
	chat = update.effective_chat
	message = update.effective_message
	if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
		if message.text.startswith('/duelo') and len(message.text) > 5:
			comando = message.text.split(' ')
			if len(comando) == 1:
				chat.bot.sendMessage(chat.id,"Você precisa indicar contra quem vai duelar")
				return
			if len(comando) > 3:
				chat.bot.sendMessage(chat.id,"Indique apenas 1 pessoa para o duelo")
				return
			if message.entities[1].type != 'mention':
				chat.bot.sendMessage(chat.id,"Você precisa indicar contra quem vai duelar")
				return

			player1 = '@'+message.from_user.username
			player2 = comando[1]

			if player1 == player2:
				chat.bot.sendMessage(chat.id,"Você não pode jogar com=ntra você mesmo")
				return

			mensagem = chat.bot.sendMessage(chat.id,
			f"{player1} invocou {player2} para um duelo de pedra, papel e tesoura",
			reply_markup=formata_botoes_telegram())

			js = json_jogos()
			js.insert_or_update(chat.id,mensagem.message_id,player1,player2)
	

def callback_botao(update: Update, context: CallbackContext) -> None:
	"""Parses the CallbackQuery and updates the message text."""
	global emojis 
	query = update.callback_query

	js = json_jogos()

	# CallbackQueries need to be answered, even if no notification to the user is needed
	# Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
	query.answer(cache_time=30)
	
	partida = js.get(query.message.chat_id,query.message.message_id)
	
	player1 = partida['player1']
	player2 = partida['player2']
	
	if query.from_user.username == player1[1:]:
		if partida['voto1'] == None:
			js.insert_or_update(query.message.chat_id,query.message.message_id,p1=player1,voto1=query.data)
	elif query.from_user.username == player2[1:]:
		if partida['voto2'] == None:
			js.insert_or_update(query.message.chat_id,query.message.message_id,p2=player2,voto2=query.data)


	texto_mensagem = f"{player1} invocou {player2} para um duelo de pedra, papel e tesoura\n\n"

	if partida['voto1'] is not None and partida['voto2'] is not None:
		texto_mensagem += f"{player1} votou {emojis[partida['voto1']]}\n"
		texto_mensagem += f"{player2} votou {emojis[partida['voto2']]}\n"
		resultado = get_result(partida)
		if resultado:
			texto_mensagem += f"Vitoria do {resultado}\n"
		else:
			texto_mensagem += "Empatou!\n"
		

	elif partida['voto1'] != None:
		texto_mensagem += f"{player1} Já votou\n"
	elif partida['voto2'] != None:
		texto_mensagem += f"{player2} Já votou\n"

	query.edit_message_text(text=texto_mensagem,reply_markup=formata_botoes_telegram())



def main() -> None:
	# Create the Updater and pass it your bot's token.
	updater = Updater(TOKEN)

	# Get the dispatcher to register handlers
	dispatcher = updater.dispatcher

	# Comandos do bot
	dispatcher.add_handler(CommandHandler('duelo', trata_comandos))

	#Callback do bot
	dispatcher.add_handler(CallbackQueryHandler(callback_botao,run_async=False))

	# Start the Bot
	updater.start_polling(allowed_updates=Update.ALL_TYPES,drop_pending_updates=True)
	updater.idle()

print ('Hora do duelo...')


if __name__ == '__main__':
	main()


