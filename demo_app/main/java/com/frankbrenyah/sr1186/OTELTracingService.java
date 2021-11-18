package com.frankbrenyah.sr1186;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Message;
import android.widget.Toast;

import androidx.annotation.NonNull;

import com.frankbrenyah.sr1186.databinding.ActivityMainBinding;
import com.google.android.material.snackbar.Snackbar;

import java.util.concurrent.TimeUnit;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;

public class OTELTracingService extends Service {
    public OTELTracingService() {
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        /*
        JaegerGrpcSpanExporter grpcExporter = JaegerGrpcSpanExporter.newBuilder()
                .setEndpoint("dev-collector.fetchrewards.com:4317")
                .setDeadlineMs(30000)   // 30 sec timeout
                .setServiceName(String.valueOf(R.string.service_name))
                .build();
        */

        OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                .setEndpoint("http://dev-collector.fetchrewards.com:4317")
                .setTimeout(30, TimeUnit.SECONDS)
                //.setCompression("gzip")
                //.addHeader("foo", "bar")
                .build();

        OpenTelemetrySdk otelSDK = OpenTelemetrySdk.builder()
                .setTracerProvider(
                        SdkTracerProvider.builder()
                                .addSpanProcessor(SimpleSpanProcessor.create(exporter))
                                //.addSpanProcessor(SimpleSpanProcessor.create(grpcExporter))
                                .setSampler(Sampler.alwaysOn())
                                .build()
                )
                .build();

        //Tracer trace = otelSDK.getTracer(name);
        Tracer trace = otelSDK.getTracer("OTEL Test App");
        Span span = trace.spanBuilder("App: Start")
                .startSpan()
                .setAttribute("service.name", R.string.service_name)
                .setAttribute("env", R.string.environment)
                .addEvent("App Launch");

        if (span.isRecording()) {
            span.setStatus(StatusCode.OK);
            try {
                // Pretend to do stuff for 500ms
                Thread.sleep(500);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            span.end();
        } else {
            span.setStatus(StatusCode.ERROR);
        }

        // Stop the service
        stopSelf();

        // If we get killed, after returning from here, restart
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        // We don't provide binding, so return null
        return null;
    }
}