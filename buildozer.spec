[app]
title = Mis Notas
package.name = misnotas
package.domain = org.juanri
source.dir = .
source.include_exts = py,png,jpg,kv,db
version = 0.1

# REQUISITOS ACTUALIZADOS: Añadimos pyobjus para que funcionen las alertas en iOS
requirements = python3,kivy==2.2.1,kivymd==1.1.1,plyer,pyobjus

orientation = portrait

# PERMISOS PARA iOS: Esto es vital para los recordatorios
ios.plist.NSUserNotificationUsageDescription = Esta aplicación necesita enviarte avisos para tus notas programadas.

# (Configuración del sistema)
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.codesign.allowed = false

[buildozer]
log_level = 2

warn_on_root = 1
