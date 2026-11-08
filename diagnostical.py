from utils import isGreaterThanOrEqualsToStart, isSmallerThanEnd

class Span:

    def __init__(
        self,
        start: tuple[int, int],
        end: tuple[int, int]
    ):
        self.start = start
        self.end = end

    def __add__(self, other) -> Span | None:
        if isinstance(other, Span):
            return Span(self.start, other.end)

        return None

    def __eq__(self, other) -> bool:
        if isinstance(other, Span):
            return self.start == other.start and self.end == other.end

        return False

    def __ne__(self, other) -> bool:
        if isinstance(other, Span):
            return self.start == other.start and self.end == other.end

        return False

class Diagnostics:

    def __init__(
        self,
        msg: str,
        rule: str,
        span: Span,
        smsg: str | None = None, # secodary msg
        _help: str | None = None, # optional help
    ):
        self.msg = msg
        self.rule = rule
        self.span = span
        self.smsg = smsg
        self.help = _help

    def __eq__(self, other):

        if (not isinstance(other, Diagnostics)
        or self.span != other.span
        or self.msg != other.msg
        or self.rule != other.rule): return False

        return True

    def __ne__(self, other):

        if (not isinstance(other, Diagnostics)
        or self.span != other.span
        or self.msg != other.msg
        or self.rule != other.rule): return False

        return True

class DiagContext:

    def __init__(self, src):
        self.seen = []
        self.src = src.split('\n')

    def emit(self, diag: Diagnostics):

        for s in self.seen:
            if s == diag: return

        self.seen.append(diag)

    def render(self):

        for s in self.seen:
            end_len = len(str(s.span.end[0]+1))
            
            print(f"compile time error[{s.rule}]: {s.msg}")
            print(' '*end_len + '|')
            render_text(self.src, s, end_len)
            print(' '*end_len + '|')
            if s.help:
                print(' '*end_len + f"= help: {s.help}")

            print('\n')

    def has_error(self):
        return len(self.seen) > 0


def render_text(src, diag, end_len):

    for row in range(diag.span.start[0], diag.span.end[0]):
        # the snippet
        if end_len > len(str(row)):
            print(' '*(end_len - len(str(row))) + str(row+1) + '|' + src[row])
        else:
            print(str(row+1) + '|' + src[row])

        # the indicator
        print(' '*(end_len) + '|', end='')
        
        for col in range(len(src[row])):

            if src[row][col] == '\t':
                print(' '*(6 - end_len), end='')
                print('—', end='')
                continue

            if (isGreaterThanOrEqualsToStart((row, col), diag.span.start)
            and isSmallerThanEnd((row, col), diag.span.end)):
                print('^', end='')
            else:
                print('—', end='')

        if diag.smsg and isGreaterThanOrEqualsToStart(diag.span.end, (row, col)): #only at the last line
            print(" ",diag.smsg, end='')

        print()
    return
