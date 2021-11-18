package com.frankbrenyah.sr1186;

import android.app.IntentService;
import android.content.Intent;

import java.util.concurrent.TimeUnit;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.otlp.http.trace.OtlpHttpSpanExporter;
import io.opentelemetry.exporters.jaeger.JaegerGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;

public class OTELService extends IntentService {

    public OTELService() {
        super("OTELService");
    }

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
    }
}
