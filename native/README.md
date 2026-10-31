# Gym 45 для iPhone

Нативная оболочка вокруг того же `index.html`. Что даёт по сравнению с браузером:

- **уведомление «Отдых окончен»** при заблокированном экране — со звуком;
- **напоминания о тренировках** по выбранным дням («🔔 Напоминания в календарь» → «Напоминать в приложении»);
- **экран не гаснет** во время тренировки (плагин KeepAwake);
- **звук таймеров** в беззвучном режиме (после правки ниже);
- облако — то же, что у версии на GitHub (Firebase, вход по почте).

## Один раз на Маке

Нужны: Xcode (из App Store), Node.js 20+ (nodejs.org), аккаунт Apple Developer для публикации.

```bash
git clone https://github.com/e87779282244-max/GYM-45.git
cd GYM-45/native
npm install
npm run web
npx cap add ios
npm run open
```

Откроется Xcode. Дальше:

1. Слева выбрать **App** → вкладка **Signing & Capabilities** → **Team**: свой аккаунт Apple.
2. Там же **+ Capability** → **Background Modes** → галочка **Audio, AirPlay, and Picture in Picture** (звук таймера при беззвучном режиме).
3. Открыть `App/AppDelegate.swift`, в начало функции `application(_:didFinishLaunchingWithOptions:)` вставить:

   ```swift
   try? AVAudioSession.sharedInstance().setCategory(.playback, options: [.mixWithOthers])
   ```

   и в самом верху файла — `import AVFoundation`.
4. Подключить iPhone кабелем, выбрать его сверху и нажать ▶ — приложение установится на телефон.

## После каждого изменения приложения

```bash
cd GYM-45 && git pull
cd native && npm run sync
```

и снова ▶ в Xcode. Для App Store: **Product → Archive → Distribute App**.

## Иконка и заставка

Положить картинку 1024×1024 в `ios/App/App/Assets.xcassets/AppIcon.appiconset` (Xcode сам предложит размеры).
