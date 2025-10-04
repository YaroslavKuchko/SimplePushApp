package com.example.simplepush;

import android.app.Activity;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.NotificationCompat;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class MainActivity extends AppCompatActivity {
    
    private static final String TAG = "SimplePushApp";
    private static final String SERVER_URL = "http://138.124.113.77:8000";
    private static final String PREFS_NAME = "device_config";
    private static final String KEY_DEVICE_TOKEN = "device_token";
    private static final String KEY_REGISTERED = "registered";
    
    private TextView statusTextView;
    private Button getLinkButton;
    private String deviceToken;
    private boolean registered = false;
    private ScheduledExecutorService backgroundExecutor;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Инициализация UI
        statusTextView = findViewById(R.id.statusTextView);
        getLinkButton = findViewById(R.id.getLinkButton);
        
        // Создание канала уведомлений
        createNotificationChannel();
        
        // Инициализация приложения
        initializeApp();
        
        // Настройка кнопки
        getLinkButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                getLinkFromServer();
            }
        });
    }
    
    private void initializeApp() {
        // Загружаем или создаем device token
        deviceToken = loadOrCreateDeviceToken();
        Log.d(TAG, "Device token: " + deviceToken.substring(0, 8) + "...");
        
        // Проверяем статус регистрации
        if (isDeviceRegistered()) {
            statusTextView.setText("✅ Уже зарегистрировано");
            registered = true;
            Log.d(TAG, "Device already registered");
        } else {
            statusTextView.setText("⏳ Регистрация...");
            registerDevice();
        }
        
        // Запускаем фоновые задачи
        startBackgroundTasks();
        
        // Получаем первую ссылку
        getLinkFromServer();
    }
    
    private String loadOrCreateDeviceToken() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String token = prefs.getString(KEY_DEVICE_TOKEN, null);
        
        if (token == null) {
            token = UUID.randomUUID().toString();
            saveDeviceToken(token);
            Log.d(TAG, "Created new device token: " + token.substring(0, 8) + "...");
        } else {
            Log.d(TAG, "Loaded existing device token: " + token.substring(0, 8) + "...");
        }
        
        return token;
    }
    
    private void saveDeviceToken(String token) {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(KEY_DEVICE_TOKEN, token);
        editor.apply();
        Log.d(TAG, "Device token saved");
    }
    
    private boolean isDeviceRegistered() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return prefs.getBoolean(KEY_REGISTERED, false);
    }
    
    private void saveRegistrationStatus(boolean registered) {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putBoolean(KEY_REGISTERED, registered);
        editor.apply();
        Log.d(TAG, "Registration status saved: " + registered);
    }
    
    private void registerDevice() {
        new AsyncTask<Void, Void, Boolean>() {
            @Override
            protected Boolean doInBackground(Void... voids) {
                try {
                    URL url = new URL(SERVER_URL + "/register_device");
                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setRequestMethod("POST");
                    connection.setRequestProperty("Content-Type", "application/json");
                    connection.setDoOutput(true);
                    
                    JSONObject jsonData = new JSONObject();
                    jsonData.put("device_token", deviceToken);
                    
                    OutputStream outputStream = connection.getOutputStream();
                    outputStream.write(jsonData.toString().getBytes());
                    outputStream.flush();
                    outputStream.close();
                    
                    int responseCode = connection.getResponseCode();
                    Log.d(TAG, "Registration response code: " + responseCode);
                    
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                        StringBuilder response = new StringBuilder();
                        String line;
                        while ((line = reader.readLine()) != null) {
                            response.append(line);
                        }
                        reader.close();
                        
                        JSONObject responseJson = new JSONObject(response.toString());
                        Log.d(TAG, "Registration successful: " + responseJson.toString());
                        return true;
                    }
                    
                } catch (Exception e) {
                    Log.e(TAG, "Registration error: " + e.getMessage());
                }
                return false;
            }
            
            @Override
            protected void onPostExecute(Boolean success) {
                if (success) {
                    registered = true;
                    saveRegistrationStatus(true);
                    statusTextView.setText("✅ Зарегистрировано");
                    showNotification("Регистрация", "Устройство успешно зарегистрировано");
                } else {
                    statusTextView.setText("❌ Ошибка регистрации");
                    showNotification("Ошибка", "Не удалось зарегистрировать устройство");
                }
            }
        }.execute();
    }
    
    private void getLinkFromServer() {
        getLinkButton.setEnabled(false);
        getLinkButton.setText("Загрузка...");
        
        new AsyncTask<Void, Void, String>() {
            @Override
            protected String doInBackground(Void... voids) {
                try {
                    URL url = new URL(SERVER_URL + "/get_link");
                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setRequestMethod("GET");
                    
                    int responseCode = connection.getResponseCode();
                    Log.d(TAG, "Get link response code: " + responseCode);
                    
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                        StringBuilder response = new StringBuilder();
                        String line;
                        while ((line = reader.readLine()) != null) {
                            response.append(line);
                        }
                        reader.close();
                        
                        JSONObject responseJson = new JSONObject(response.toString());
                        String link = responseJson.optString("link", "https://google.com");
                        Log.d(TAG, "Link received: " + link);
                        return link;
                    }
                    
                } catch (Exception e) {
                    Log.e(TAG, "Get link error: " + e.getMessage());
                }
                return null;
            }
            
            @Override
            protected void onPostExecute(String link) {
                getLinkButton.setEnabled(true);
                getLinkButton.setText("Получить ссылку");
                
                if (link != null) {
                    openUrl(link);
                    showNotification("Ссылка получена", "Ссылка: " + link);
                    vibrate();
                } else {
                    Toast.makeText(MainActivity.this, "Ошибка получения ссылки", Toast.LENGTH_SHORT).show();
                }
            }
        }.execute();
    }
    
    private void openUrl(String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            startActivity(intent);
            Log.d(TAG, "URL opened: " + url);
        } catch (Exception e) {
            Log.e(TAG, "Error opening URL: " + e.getMessage());
            Toast.makeText(this, "Не удалось открыть ссылку", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void startBackgroundTasks() {
        backgroundExecutor = Executors.newScheduledThreadPool(1);
        
        // Проверка регистрации каждые 30 секунд
        backgroundExecutor.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                if (!registered) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            registerDevice();
                        }
                    });
                }
            }
        }, 30, 30, TimeUnit.SECONDS);
        
        // Получение ссылки каждые 60 секунд
        backgroundExecutor.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                getLinkFromServer();
            }
        }, 60, 60, TimeUnit.SECONDS);
        
        Log.d(TAG, "Background tasks started");
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "SimplePush Notifications";
            String description = "Notifications for SimplePush app";
            int importance = NotificationManager.IMPORTANCE_DEFAULT;
            NotificationChannel channel = new NotificationChannel("simplepush_channel", name, importance);
            channel.setDescription(description);
            
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }
    
    private void showNotification(String title, String message) {
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, "simplepush_channel")
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(message)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT);
        
        NotificationManager notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify((int) System.currentTimeMillis(), builder.build());
    }
    
    private void vibrate() {
        Vibrator vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        if (vibrator != null && vibrator.hasVibrator()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(1000, VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                vibrator.vibrate(1000);
            }
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (backgroundExecutor != null) {
            backgroundExecutor.shutdown();
        }
    }
}
