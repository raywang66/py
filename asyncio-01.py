import asyncio

async def myCoroutine():
    """ Define a coroutine that takes in a future

    :return:
    """
    print("My Coroutine")


def main():
    """ Spin up a quick and simple event loop and run until completed

    :return:
    """
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(myCoroutine())
    finally:
        loop.close()


if __name__ == '__main__':
    main()

