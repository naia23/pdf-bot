import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PyPDF2 import PdfMerger
import logging

TOKEN = "8956457759:AAGcFE4Md-FtI6ipIXa9O6FnB7y9cU2tZ_s"

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Diccionario para almacenar archivos por usuario
user_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 ¡Hola! Soy tu bot de PDF.\n\n"
        "📤 Envíame varios PDFs uno tras otro.\n"
        "🔗 Cuando termines, usa /merge para unirlos.\n"
        "🏷️ Usa /rename para cambiar el nombre del PDF final.\n"
        "🗑️ Usa /clear para borrar tu lista."
    )

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    document = update.message.document
    
    # Verificar que sea PDF
    if not document.file_name.endswith('.pdf'):
        await update.message.reply_text("❌ Solo acepto archivos PDF.")
        return
    
    # Descargar el archivo
    file = await context.bot.get_file(document.file_id)
    
    # Guardar temporalmente
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{user_id}_{document.file_name}")
    await file.download_to_drive(file_path)
    
    # Almacenar en la lista del usuario
    if user_id not in user_files:
        user_files[user_id] = []
    user_files[user_id].append(file_path)
    
    await update.message.reply_text(f"✅ PDF guardado: {document.file_name}\n\n📊 Tienes {len(user_files[user_id])} PDF(s) en tu lista.\n🔗 Usa /merge cuando quieras unirlos.")

async def merge_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_files or not user_files[user_id]:
        await update.message.reply_text("❌ No tienes PDFs guardados. Envía algunos primero.")
        return
    
    merger = PdfMerger()
    
    try:
        for pdf_path in user_files[user_id]:
            merger.append(pdf_path)
        
        # Guardar PDF unido
        output_path = os.path.join(tempfile.gettempdir(), f"{user_id}_merged.pdf")
        merger.write(output_path)
        merger.close()
        
        # Enviar al usuario
        with open(output_path, 'rb') as f:
            await update.message.reply_document(document=f, filename="documento_unido.pdf")
        
        await update.message.reply_text("✅ PDFs unidos correctamente.\n\n🏷️ Usa /rename <nombre> para cambiarle el nombre.")
        
        # Guardar la ruta del último PDF para renombrarlo
        context.user_data['last_pdf'] = output_path
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al unir: {str(e)}")

async def rename_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Obtener el nuevo nombre
    if not context.args:
        await update.message.reply_text("❌ Uso: /rename <nombre_del_archivo>\nEjemplo: /rename mi_novela_completa")
        return
    
    new_name = ' '.join(context.args)
    if not new_name.endswith('.pdf'):
        new_name += '.pdf'
    
    # Buscar el último PDF generado
    last_pdf = context.user_data.get('last_pdf')
    
    if not last_pdf or not os.path.exists(last_pdf):
        await update.message.reply_text("❌ No hay ningún PDF reciente para renombrar. Usa /merge primero.")
        return
    
    # Renombrar el archivo
    new_path = os.path.join(os.path.dirname(last_pdf), new_name)
    os.rename(last_pdf, new_path)
    context.user_data['last_pdf'] = new_path
    
    await update.message.reply_text(f"✅ PDF renombrado a: {new_name}")

async def clear_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_files:
        # Eliminar archivos temporales
        for pdf_path in user_files[user_id]:
            try:
                os.remove(pdf_path)
            except:
                pass
        user_files[user_id] = []
    
    await update.message.reply_text("🗑️ Lista de PDFs borrada.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clear_files(update, context)
    await update.message.reply_text("✅ Sesión cancelada. Puedes empezar de nuevo.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("merge", merge_pdfs))
    app.add_handler(CommandHandler("rename", rename_pdf))
    app.add_handler(CommandHandler("clear", clear_files))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    
    print("🤖 Bot de PDF iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()