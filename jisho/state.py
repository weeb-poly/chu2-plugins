from typing import Callable, ClassVar, Optional
import logging

import discord


class MessageState:
    author: discord.User
    message: discord.Message
    callback: Callable

    def __init__(self, author, message, callback):
        self.author = author
        self.message = message
        self.callback = callback

    def __str__(self) -> str:
        return f'MessageState(author={self.author}, message={self.message}, callback={self.callback})'


class MessageStateQuery(MessageState):
    """
    Holds information about a jisho-bot search query
    """

    query: str
    response: dict
    offset: int

    def __init__(self, author, query, response, message, offset, callback) -> None:
        super().__init__(author, message, callback)

        self.query = query
        self.response = response
        self.offset = offset

    def __str__(self):
        return f'MessageStateQuery(author={self.author}, query={self.query}, response={self.response}, message={self.message}, offset={self.offset}, callback={self.callback})'


class Node:
    """
    Represents a node in a linked list
    """

    value: MessageState
    next: Optional['Node']
    
    def __init__(self, value, next=None) -> None:
        self.value = value
        self.next = next


class MessageCache:
    """
    Holds message states in a LRU cache implemented with a linked list
    """

    __KEYERROR_MESSAGE: ClassVar[str] = 'Message not found in cache'

    maxsize: int
    head: Optional[Node]
    size: int

    def __init__(self, maxsize: int) -> None:
        self.maxsize = maxsize
        self.head = None
        self.size = 0

    async def insert(self, state: MessageState) -> None:
        """
        Inserts a new message state at the head of the cache, evicts as necessary

        :param messagestate: message state to add to cache
        :return: nothing
        """
        # Insert at front (safe for empty cache)
        newnode = Node(state, self.head)
        self.head = newnode
        self.size += 1

        # Eviction check
        while self.size > self.maxsize:
            await self._evict()

    async def _evict(self) -> None:
        """
        Helper method to evict least recently used message state, calling callback with message as parameter on eviction

        :return: nothing
        """

        # Can't evict on empty list
        if not self.head:
            return

        # Evict only element
        if self.size == 1:
            await self.head.value.callback(self.head.value.message)

            self.head = None
            self.size -= 1

        # Evict element at end
        else:
            prev = None
            curr = self.head

            for _i in range(self.size - 1):
                prev, curr = curr, curr.next

            await curr.value.callback(curr.value.message)

            prev.next = None
            self.size -= 1

    def __getitem__(self, item: discord.Message) -> MessageState:
        """
        Finds a message state by using the message as the key

        :param item: discord message to look for
        :return: message state corresponding to input message
        :raises KeyError: message not found in cache
        """

        # If cache is empty, raise error
        if not self.head:
            raise KeyError(MessageCache.__KEYERROR_MESSAGE)

        # If message is found at head, no need for rearranging
        elif self.head.value.message == item:
            return self.head.value

        # Search rest of cache, if it exists
        else:
            prev = self.head
            curr = prev.next

            # Loop through linked list until end of list or message found
            while curr and not curr.value.message == item:
                prev, curr = curr, curr.next

            # Raise KeyError if not found
            if not curr:
                raise KeyError(MessageCache.__KEYERROR_MESSAGE)

            # Move found node to front of list
            prev.next = curr.next
            curr.next = self.head
            self.head = curr

            return curr.value

    async def remove(self, message: discord.Message) -> None:
        """
        Removes a message state from the cache using the message as the key, does not call callback

        :param message: message state's message to remove
        :return: nothing
        :raises KeyError: message not found in cache
        """

        # Move message to remove to head
        self.__getitem__(message)

        # Remove head
        self.head = self.head.next
        self.size -= 1

    def print_status(self) -> None:
        """
        Debugging helper method for printing the status of the message cache

        :return: nothing
        """

        logging.info(f'MessageCache: {self.size} items stored out of a max of {self.maxsize}')
    
        i = 0
        curr = self.head
        while curr:
            print(f'[{i}]: {curr.value}')
            i += 1
            curr = curr.next
