if __name__ == "__main__":
    from gpt4all import GPT4All

    model = GPT4All("mistral-7b-openorca.Q4_0.gguf")
    # print(model.list_models())
    output = model.generate("тайтл для поста с емодзи - рецепт пирожков с луком", n_predict=2)
    print(output)