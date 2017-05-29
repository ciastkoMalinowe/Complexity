from multiprocessing import Process, Pipe


class Timeout:
    class TimeoutException(Exception):
        def __init__(self, **kwargs):
            self.x = kwargs.get('x', [])
            self.y = kwargs.get('y', [])

    def __init__(self, sec):
        self.sec = sec

    def __call__(self, fun):
        def wrap(*args, **kwargs):
            def child(pipe):
                result = fun(*args, **kwargs)
                pipe.send(result)
                pipe.close()

            parent_pipe, child_pipe = Pipe()

            process = Process(target=child, args=(child_pipe,))
            process.start()
            process.join(self.sec)

            if process.is_alive():
                process.terminate()
                process.join()
                raise Timeout.TimeoutException(**kwargs)
            result = parent_pipe.recv()
            parent_pipe.close()
            return result

        return wrap
