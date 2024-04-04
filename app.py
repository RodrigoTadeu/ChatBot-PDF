from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores.faiss import FAISS
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from flask import Flask, jsonify, request
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import database
import uuid

app = Flask(__name__)
load_dotenv()
lista_dados = []


@app.route('/iniciarSessao', methods=['GET', 'POST'])
def iniciarSessao():
    sessao = {'token': generate_session_id(), 'status': 'Sessao iniciada'}

    database.create_session(sessao['token'])

    return jsonify(sessao)


@app.route('/enviarPdf', methods=['GET', 'POST'])
def enviarPdf():
    pdf = request.get_json()

    if pdf['token'] == "":
        return jsonify({'error': 'Campo token vazio'}), 400

    texto_pdf = pdf['pdf']

    row = database.verify_pdf(pdf['token'])

    if row is None:
        return jsonify({'error': 'Token invalido'}), 400
    if row and row[0]:
        texto_pdf = row[0] + ' \n ' + pdf['pdf']

    database.insert_pdf(texto_pdf, pdf['token'])
    select = database.select_pdf(pdf['token'])

    for dado in lista_dados:
        if dado["token"] == pdf["token"]:
            lista_dados.remove(dado)

    text_chunks = get_text_chunks(select[0])
    vectorstore = get_vectorstore(text_chunks)
    texto = get_conversation_chain(vectorstore)

    dados = {"token": pdf['token'], "texto": texto}
    lista_dados.append(dados)

    return jsonify({'status': "Pdf armazenado com sucesso"})


@app.route('/retornarResposta', methods=['GET', 'POST'])
def retornarResposta():
    pergunta = request.get_json()
    resposta = ""

    for dado in lista_dados:
        if pergunta['token'] == dado["token"]:
            resposta = handle_userinput(dado['texto'], pergunta['pergunta'])
            break

    if resposta == "":
        rowcount = database.delete_session(pergunta['token'])
        if rowcount == 0:
            resposta = "Token invalido"
        else:
            resposta = "Esta sessão não existe mais, crie um novo usuário."

    return jsonify({'resposta': resposta})


@app.route('/encerrarSessao', methods=['GET', 'POST'])
def encerrarSessao():
    encerrar = request.get_json()

    if encerrar['token'] == "":
        return jsonify({'error': 'Campo token vazio'}), 400

    rowcount = database.delete_session(encerrar['token'])

    if rowcount == 0:
        return jsonify({'error': 'Token invalido'}), 404

    for dado in lista_dados:
        if dado["token"] == encerrar['token']:
            lista_dados.remove(dado)

    status = {'status': 'Sessão encerrada com sucesso'}

    return jsonify(status)


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(text_chunks, embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={'k': 1}),
        memory=memory,
        verbose=True
    )
    return conversation_chain


def handle_userinput(obj_texto, user_question):
    response = obj_texto.invoke({'question': user_question})
    chat_history = response['chat_history']
    resposta_chat = chat_history[-1].content
    return resposta_chat


def generate_session_id():
    return str(uuid.uuid4())


if __name__ == "__main__":
    database.create_table()
    app.run(host='0.0.0.0', port='5552', debug=True)
