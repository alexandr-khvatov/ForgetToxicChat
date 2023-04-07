from aiogram import Router
from aiogram.types import Message
from filters.chat_type import ChatTypeFilter

from services.toxicity.BertToxicityClassifier import BertToxicityClassifier, get_model

router: Router = Router()


@router.message(ChatTypeFilter(chat_type=["group", "supergroup"]))
async def process_moderator(message: Message, model: BertToxicityClassifier):
    # model: BertToxicityClassifier = get_model()

    confidence, probs, predicted_class, label = model.predict(message.text)
    if predicted_class == 1:
        await message.delete()
    # send debug message
    msg = f'''
    confidence: {confidence:.2f},
    probs: {list(map(lambda x: format(x, '.2f'),probs))},
    label: {predicted_class} = {label}
    '''
    await message.answer(text=msg)
    # send debug message

    # if "kk" in str(message.text):
    #     await message.delete()
    #     await message.answer(text="Собщение удалено")
    # # else:
    # #     await message.answer(text=LEXICON_RU['other_answer'])


# check the message is not from the group
def check_the_message_is_not_from_the_group(message: Message) -> bool:
    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        return True
    return False
