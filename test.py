

def test():
    with open("sowpods.txt") as f:
        two_let_a_words = []
        good_words = set(x.strip().lower() for x in f.readlines())
        for word in good_words:
            if len(word) == 3 and 'a' in word:
                two_let_a_words.append(word)
                print(word)
        print("Total: ", len(two_let_a_words))

test()
