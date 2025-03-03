import asyncio, re, ast, time, math, logging, random, pyrogram, shutil, psutil 

# Pyrogram Functions
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums 
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid

# Helper Function
from Script import script
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, get_shortlink, get_time, humanbytes 

# Database Function 
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import del_all, find_filter, get_filters
from database.gfilters_mdb import find_gfilter, get_gfilters
from database.users_chats_db import db


# Configuration
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, PICS, IMDB, PM_IMDB, SINGLE_BUTTON, PROTECT_CONTENT, \
    SPELL_CHECK_REPLY, IMDB_TEMPLATE, IMDB_DELET_TIME, START_MESSAGE, PMFILTER, G_FILTER, BUTTON_LOCK, BUTTON_LOCK_TEXT, SHORT_URL, SHORT_API


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)



@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
        
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    return await query.message.edit_text("Make Sure I'm Present In Your Group!!", quote=True)
            else:
                return await query.message.edit_text("I'm Not Connected To Any Groups!\ncheck /Connections Or Connect To Any Groups", quote=True)
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title
        else: return
        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS): await del_all(query.message, grp_id, title)
        else: await query.answer("You Need To Be Group Owner Or An Auth User To Do That!", show_alert=True)
        
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try: await query.message.reply_to_message.delete()
                except: pass
            else: await query.answer("Buddy, Don't Touch Others' Property! 😁\nदोस्त, दूसरों की संपत्ति को मत छूना! 😁", show_alert=True)

            
    elif "groupcb" in query.data:
        group_id = query.data.split(":")[1]
        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        if act == "":
            stat = "Connect"
            cb = "connectcb"
        else:
            stat = "Disconnect"
            cb = "disconnect"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
            InlineKeyboardButton("Delete", callback_data=f"deletecb:{group_id}")
            ],[
            InlineKeyboardButton("Back", callback_data="backcb")]
        ])
        await query.message.edit_text(f"Group Name:- **{title}**\nGroup Id:- `{group_id}`", reply_markup=keyboard, parse_mode=enums.ParseMode.MARKDOWN)
      
    elif "connectcb" in query.data:
        group_id = query.data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkact = await make_active(str(user_id), str(group_id))
        if mkact: await query.message.edit_text(f"Connected To: **{title}**", parse_mode=enums.ParseMode.MARKDOWN,)
        else: await query.message.edit_text('Some Error Occurred!!', parse_mode="md")
       
    elif "disconnect" in query.data:
        group_id = query.data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkinact = await make_inactive(str(user_id))
        if mkinact: await query.message.edit_text(f"Disconnected From **{title}**", parse_mode=enums.ParseMode.MARKDOWN)
        else: await query.message.edit_text(f"Some Error Occurred!!", parse_mode=enums.ParseMode.MARKDOWN)
      
    elif "deletecb" in query.data:
        user_id = query.from_user.id
        group_id = query.data.split(":")[1]
        delcon = await delete_connection(str(user_id), str(group_id))
        if delcon: await query.message.edit_text("Successfully Deleted Connection")
        else: await query.message.edit_text(f"Some Error Occurred!!", parse_mode=enums.ParseMode.MARKDOWN)
       
    elif query.data == "backcb":
        userid = query.from_user.id
        groupids = await all_connections(str(userid))
        if groupids is None:
            return await query.message.edit_text("There Are No Active Connections!! Connect To Some Groups First.")
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append([InlineKeyboardButton(f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}")])
            except: pass
        if buttons: await query.message.edit_text("Your Connected Group Details ;\n\n", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]        
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)       
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    elif "galert" in query.data:
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]             
        reply_text, btn, alerts, fileid = await find_gfilter("gfilters", keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    
    if query.data.startswith("pmfile"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('No Such File Exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)                                                                                                      
            except Exception as e: logger.exception(e)
        try:                  
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            else:
                await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == "pmfilep" else False)                       
        except Exception as e:
            await query.answer(f"⚠️ Eʀʀᴏʀ {e}", show_alert=True)
        
    if query.data.startswith("file"):        
        ident, req, file_id = query.data.split("#")
        if BUTTON_LOCK:
            if int(req) not in [query.from_user.id, 0]:
                return await query.answer(BUTTON_LOCK_TEXT.format(query=query.from_user.first_name), show_alert=True)
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('No Such File Exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)                               
            except Exception as e: logger.exception(e)
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            elif settings['botpm']:
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            else:
                await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == "filep" else False)
                await query.answer('Cʜᴇᴄᴋ PM, I Hᴀᴠᴇ Sᴇɴᴛ Fɪʟᴇs Iɴ Pᴍ', show_alert=True)
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ Tʜᴇ Bᴏᴛ Mᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
     
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            return await query.answer("I Lɪᴋᴇ Yᴏᴜʀ Sᴍᴀʀᴛɴᴇss, Bᴜᴛ Dᴏɴ'ᴛ Bᴇ Oᴠᴇʀsᴍᴀʀᴛ Oᴋᴀʏ 😏", show_alert=True)
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('NO SUCH FILE EXIST....')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)  
            except Exception as e: logger.exception(e)
        await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == 'checksubp' else False)
    elif query.data == "pages":
        await query.answer("🤨 Cᴜʀɪᴏsɪᴛʏ Is A Lɪᴛᴛʟᴇ Mᴏʀᴇ, Isɴ'ᴛ Iᴛ? 😁", show_alert=True)
    elif query.data == "howdl":
        try: await query.answer(script.HOW_TO_DOWNLOAD.format(query.from_user.first_name), show_alert=True)
        except: await query.message.edit(script.HOW_TO_DOWNLOAD.format(query.from_user.first_name))

    elif query.data == "start":                        
        buttons = [[
            InlineKeyboardButton("• Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Cʜᴀᴛ •", url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],[
            InlineKeyboardButton("Sᴇᴀʀᴄʜ 🔎", switch_inline_query_current_chat=''), 
            InlineKeyboardButton(" 📌 Cʜᴀɴɴᴇʟ", url="https://t.me/kissuxbots")
            ],[      
            InlineKeyboardButton("Hᴇʟᴩ 🦧", callback_data="help"),
            InlineKeyboardButton("Aʙᴏᴜᴛ 😜", callback_data="about")
        ],[
            InlineKeyboardButton('Hᴇʟᴘᴅᴇꜱᴋ 🦫', url=f'https://t.me/kissuhelp')
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), START_MESSAGE.format(user=query.from_user.mention, bot=client.mention), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
       
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('✉️ ᴀɴʏ ǫᴜᴇʀʏ ✉️', url='t.me/kissu_help_bot')
        ],[
            InlineKeyboardButton('⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ ⚙️', 'admin')            
            ],[
            InlineKeyboardButton('Fɪʟᴛᴇʀꜱ', 'openfilter'),
            InlineKeyboardButton('Cᴏɴɴᴇᴄᴛ', 'coct')
            ],[                       
            InlineKeyboardButton('Bᴏᴛ Sᴛᴀᴛᴜꜱ ❄️', 'stats'),
            InlineKeyboardButton('Exᴛʀᴀ Mᴏᴅᴇ', 'extmod')
            ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'start')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.HELP_TXT.format(query.from_user.mention), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))     
        
    elif query.data == "about":
        buttons= [[
            InlineKeyboardButton('Sᴏᴜʀᴄᴇ Cᴏᴅᴇ 📜', 'source')
            ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'start')          
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.ABOUT_TXT.format(temp.B_NAME), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('Hᴇʟᴘᴅᴇꜱᴋ 🦫', url=f'https://t.me/kissuhelp')
        ],[
            InlineKeyboardButton('‹ Bᴀᴄᴋ', 'about')
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.SOURCE_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
      
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        if query.from_user.id not in ADMINS:
            return await query.answer("Sᴏʀʀʏ Tʜɪs Mᴇɴᴜ Oɴʟʏ Fᴏʀ Mʏ Aᴅᴍɪɴs ⚒️", show_alert=True)
        await query.message.edit("Pʀᴏᴄᴇꜱꜱɪɴɢ Wᴀɪᴛ Fᴏʀ 15 ꜱᴇᴄ...")
        total, used, free = shutil.disk_usage(".")
        stats = script.SERVER_STATS.format(get_time(time.time() - client.uptime), psutil.cpu_percent(), psutil.virtual_memory().percent, humanbytes(total), humanbytes(used), psutil.disk_usage('/').percent, humanbytes(free))            
        stats_pic = await make_carbon(stats, True)
        await query.edit_message_media(InputMediaPhoto(stats_pic, script.ADMIN_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "openfilter":
        buttons = [[
            InlineKeyboardButton('AᴜᴛᴏFɪʟᴛᴇʀ', 'autofilter'),
            InlineKeyboardButton('MᴀɴᴜᴀʟFɪʟᴛᴇʀ', 'manuelfilter')
            ],[
            InlineKeyboardButton('GʟᴏʙᴀʟFɪʟᴛᴇʀ', 'globalfilter')
            ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.FILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'openfilter')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.AUTOFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('Bᴜᴛᴛᴏɴ Fᴏʀᴍᴀᴛ', 'button')
            ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'openfilter')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.MANUELFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "globalfilter":
        buttons = [[
            InlineKeyboardButton('Bᴜᴛᴛᴏɴ Fᴏʀᴍᴀᴛ', 'buttong')
            ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'openfilter')           
        ]]
        if query.from_user.id not in ADMINS:
            return await query.answer("Sᴏʀʀʏ Tʜɪs Mᴇɴᴜ Oɴʟʏ Fᴏʀ Mʏ Aᴅᴍɪɴs ⚒️", show_alert=True)
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.GLOBALFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data.startswith("button"):
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', f"{'manuelfilter' if query.data == 'button' else 'globalfilter'}")           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.BUTTON_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
   
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.CONNECTION_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
         
    elif query.data == "newdata":
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.FILE_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "extmod":
        buttons = [[
            InlineKeyboardButton('🎭 Sᴛɪᴄᴋᴇʀ_ɪᴅ ⚜️', callback_data='sticker')
        ],[ 
            InlineKeyboardButton('🙌 Fᴏɴᴛ Gᴇɴᴇʀᴀᴛᴏʀ 📝', callback_data='font')
        ],[
            InlineKeyboardButton('🔭 Sᴛᴀᴛs 📊', callback_data='stats')
        ],[
            InlineKeyboardButton('🌐 ᴄᴏᴜɴᴛʀʏ 🔅', callback_data='country')
        ],[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.EXTRAMOD_TXT, enums.ParseMode.HTML),             reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "gpmanager":
        buttons = [[
            InlineKeyboardButton('✘ Cʟᴏꜱᴇ', 'close_data'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.GROUPMANAGER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))           
        
    elif query.data == "country":
        buttons = [[
            InlineKeyboardButton('‹‹‹ Bᴀᴄᴋ', callback_data='mods')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CON_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "sticker":
        buttons = [[
            InlineKeyboardButton('‹‹‹ Bᴀᴄᴋ', callback_data='mods')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.STICKER_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "font":
        buttons = [[
            InlineKeyboardButton('‹‹‹ Bᴀᴄᴋ', callback_data='mods')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FONT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('⟳ Rᴇꜰʀᴇꜱʜ', 'stats'),
            InlineKeyboardButton('« Bᴀᴄᴋ', 'help')           
        ]]
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit('ʟᴏᴀᴅɪɴɢ....')
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.STATUS_TXT.format(total, users, chats, monsize, free), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
    
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))
        if str(grp_id) != str(grpid):
            return await query.message.edit("Yᴏᴜʀ Aᴄᴛɪᴠᴇ Cᴏɴɴᴇᴄᴛɪᴏɴ Hᴀs Bᴇᴇɴ Cʜᴀɴɢᴇᴅ. Gᴏ Tᴏ /settings")
        if status == "True": await save_group_settings(grpid, set_type, False)
        else: await save_group_settings(grpid, set_type, True)
        settings = await get_settings(grpid)
        if settings is not None:
            buttons = [[
                InlineKeyboardButton(f"ꜰɪʟᴛᴇʀ ʙᴜᴛᴛᴏɴ : {'sɪɴɢʟᴇ' if settings['button'] else 'ᴅᴏᴜʙʟᴇ'}", f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"ꜰɪʟᴇ ɪɴ ᴩᴍ ꜱᴛᴀʀᴛ: {'ᴏɴ' if settings['botpm'] else 'ᴏꜰꜰ'}", f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],[                
                InlineKeyboardButton(f"ʀᴇꜱᴛʀɪᴄᴛ ᴄᴏɴᴛᴇɴᴛ : {'ᴏɴ' if settings['file_secure'] else 'ᴏꜰꜰ'}", f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"ɪᴍᴅʙ ɪɴ ꜰɪʟᴛᴇʀ : {'ᴏɴ' if settings['imdb'] else 'ᴏꜰꜰ'}", f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"ꜱᴩᴇʟʟɪɴɢ ᴄʜᴇᴄᴋ : {'ᴏɴ' if settings['spell_check'] else 'ᴏꜰꜰ'}", f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ : {'ᴏɴ' if settings['welcome'] else 'ᴏꜰꜰ'}", f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
            ]]
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))







