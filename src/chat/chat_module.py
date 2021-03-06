"""
CMSC 137 CD-5L Final Project: Milestone #2
Group: Quartet Mirana
    Crisostomo, Albert Dominic
    Fortes, Patricia
    Mojar, Kenneth
    Umali, Harold
"""
from chat import player_pb2 as PlayerModule
from chat import tcp_packet_pb2 as TcpPacketModule
import socket as Socket
import select
import sys

# DO NOT CHANGE;
# Client cannot 'join' when set to 'True'
IS_DISCONNECTED = False

# constants
BUFFER_SIZE  = 1024
SUCCESSFUL   = 0
UNSUCCESSFUL = 1
LOBBY_DNE    = 2
LOBBY_FULL   = 3

def initializeClient():
    return Socket.socket( Socket.AF_INET, Socket.SOCK_STREAM )

# # global client socket
server_address = ( "202.92.144.45", 80 )
client_socket  = initializeClient()

def createLobby( player_name, max_players = 4 ):

    IS_DISCONNECTED = False

    # instantiate attributes
    create_lobby_packet = TcpPacketModule.TcpPacket.CreateLobbyPacket()
    create_lobby_packet.type = TcpPacketModule.TcpPacket.CREATE_LOBBY
    create_lobby_packet.max_players = max_players
    
    # send then receive
    client_socket.sendall(create_lobby_packet.SerializeToString())
    data = client_socket.recv(BUFFER_SIZE)

    # parse received data
    create_lobby_packet = TcpPacketModule.TcpPacket.CreateLobbyPacket()
    create_lobby_packet.ParseFromString(data)
    
    # debug
    # print(create_lobby_packet)
    # print( IS_DISCONNECTED )

    # auto join creator
    status = joinLobby( create_lobby_packet.lobby_id, player_name )

    return ( status, create_lobby_packet.lobby_id )

def joinLobby( lobby_id, player_name ):

    IS_DISCONNECTED = False

    # instantiate type handler packet
    tcp_packet = TcpPacketModule.TcpPacket()

    # instantiate connect packet attributes
    connect_packet             = TcpPacketModule.TcpPacket.ConnectPacket()
    connect_packet.type        = TcpPacketModule.TcpPacket.CONNECT
    connect_packet.player.name = player_name
    connect_packet.lobby_id    = lobby_id

    # send then receive
    client_socket.sendall( connect_packet.SerializeToString() )
    data = client_socket.recv( BUFFER_SIZE )

    # parse received data
    tcp_packet.ParseFromString(data)

    # determine packet type
    if   tcp_packet.type == TcpPacketModule.TcpPacket.ERR_LDNE:
        return LOBBY_DNE
    elif tcp_packet.type == TcpPacketModule.TcpPacket.ERR_LFULL:
        return LOBBY_FULL
    elif tcp_packet.type == TcpPacketModule.TcpPacket.ERR:
        return UNSUCCESSFUL
    elif tcp_packet.type == TcpPacketModule.TcpPacket.CONNECT:
        return SUCCESSFUL


def send( message ):
    # instantiate attributes
    chat_packet = TcpPacketModule.TcpPacket.ChatPacket()
    chat_packet.type = TcpPacketModule.TcpPacket.CHAT
    chat_packet.message = message

    # # client exits
    # if chat_packet.message == "/exit":
    #     quitLobby()
    # client requests list of players currently in lobby
    # elif chat_packet.message == "/players":
    #     showAllPlayers()
    # elif chat_packet.message != "":
    client_socket.sendall(chat_packet.SerializeToString())

def receive( socks ):
    tcp_packet = TcpPacketModule.TcpPacket()

    # instantiate attributes
    data = socks.recv( BUFFER_SIZE )
    tcp_packet.ParseFromString( data )

    # received message
    if tcp_packet.type == TcpPacketModule.TcpPacket.CHAT:
        # create packet holder
        chat_packet = TcpPacketModule.TcpPacket.ChatPacket()
        chat_packet.ParseFromString( data )

        # write message
        return "<{}> {}".format( chat_packet.player.name, chat_packet.message )

    # received disconnect packet
    elif tcp_packet.type == TcpPacketModule.TcpPacket.DISCONNECT:

        # create packet holder
        disconnect_packet = TcpPacketModule.TcpPacket.DisconnectPacket()
        disconnect_packet.ParseFromString( data )

        # check packet type
        if disconnect_packet.update == TcpPacketModule.TcpPacket.DisconnectPacket.NORMAL:
            return "<SERVER> {} HAS LEFT THE CHAT LOBBY.".format( disconnect_packet.player.name )

        elif disconnect_packet.update == TcpPacketModule.TcpPacket.DisconnectPacket.LOST:
            return "<SERVER> {} LOST CONNECTION TO THE CHAT LOBBY.".format( disconnect_packet.player.name )

    # received connect packet
    elif tcp_packet.type == TcpPacketModule.TcpPacket.CONNECT:
        # create packet holder
        connect_packet = TcpPacketModule.TcpPacket.ConnectPacket()
        connect_packet.ParseFromString( data )

        return "<SERVER> {} has connected to the chat lobby.".format( connect_packet.player.name )

def quitLobby():
    IS_DISCONNECTED = True

    # instantiate attributes
    disconnect_packet      = TcpPacketModule.TcpPacket.DisconnectPacket()
    disconnect_packet.type = TcpPacketModule.TcpPacket.DISCONNECT

    client_socket.sendall( disconnect_packet.SerializeToString() )

def showAllPlayers():
    # instantiate attributes
    player_list_packet      = TcpPacketModule.TcpPacket.PlayerListPacket()
    player_list_packet.type = TcpPacketModule.TcpPacket.PLAYER_LIST

    # send and receive data from server 
    client_socket.sendall( player_list_packet.SerializeToString() )
    data = client_socket.recv( BUFFER_SIZE )

    # parse received data
    player_list_packet.ParseFromString( data )

    # display players
    sys.stdout.write("\nPlayers in Lobby\n")
    sys.stdout.write("=====================\n")
    for player in player_list_packet.player_list:
        sys.stdout.write(player.name+"\n")
    sys.stdout.write("=====================\n\n")
    sys.stdout.flush()
