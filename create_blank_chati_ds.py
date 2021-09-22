import pickle
chatids_db_file = 'chat_ids.data'
fw = open(chatids_db_file, 'wb')
pickle.dump("", fw)
