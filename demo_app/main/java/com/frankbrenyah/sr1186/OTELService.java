package com.frankbrenyah.sr1186;

import android.app.IntentService;
import android.content.Intent;

import java.util.concurrent.TimeUnit;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;

public class OTELService extends IntentService {
    /**
     * Creates an IntentService.  Invoked by your subclass's constructor.
     *
     * @param name Used to name the worker thread, important only for debugging.
     */
    public OTELService(String name) {
        super(name);
    }

    @Override
    protected void onHandleIntent(Intent workIntent) {
        // Gets data from the incoming Intent
        //String name = workIntent.getDataString();

        //Sampler traceIdRatioBased = Sampler.traceIdRatioBased(0.5);

        OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                .setEndpoint("http://dev-collector.nothing.com:4317")
                .setTimeout(60, TimeUnit.SECONDS)
                //.setCompression("gzip")
                //.addHeader("foo", "bar")
                .build();

        OpenTelemetrySdk otelSDK = OpenTelemetrySdk.builder()
                .setTracerProvider(
                        SdkTracerProvider.builder()
                                .addSpanProcessor(SimpleSpanProcessor.create(exporter))
                                .setSampler(Sampler.alwaysOn())
                                .build()
                )
                .build();

        //Tracer trace = otelSDK.getTracer(name);
        Tracer trace = otelSDK.getTracer("OTEL Test App");
        Span span = trace.spanBuilder("App: Base")
                .startSpan()
                .setAttribute("service.name", R.string.app_name)
                .setAttribute("env", R.string.environment)
                .addEvent("App Launch");

        if (span.isRecording()) {
            span.setStatus(StatusCode.OK);
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            span.end();
        } else {
            span.setStatus(StatusCode.ERROR);
        }

        // Stop the service
        stopSelf();
    }
}
