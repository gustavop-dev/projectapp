<template>
  <div class="relative w-full h-full overflow-hidden" aria-hidden="true">
    <ClientOnly>
      <canvas ref="canvasRef" class="w-full h-full block" />
    </ClientOnly>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

const canvasRef = ref(null);
let renderer = null;
let raf = null;

const vertexSrc = `#version 300 es
precision highp float;
in vec4 position;
void main(){gl_Position=position;}`;

const fragmentSrc = `#version 300 es
precision highp float;
out vec4 O;
uniform float time;
uniform vec2 resolution;

#define FC gl_FragCoord.xy
#define R resolution
#define T (time+660.)

float rnd(vec2 p){p=fract(p*vec2(12.9898,78.233));p+=dot(p,p+34.56);return fract(p.x*p.y);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p),u=f*f*(3.-2.*f);return mix(mix(rnd(i),rnd(i+vec2(1,0)),u.x),mix(rnd(i+vec2(0,1)),rnd(i+1.),u.x),u.y);}
float fbm(vec2 p){float t=.0,a=1.;for(int i=0;i<5;i++){t+=a*noise(p);p*=mat2(1,-1.2,.2,1.2)*2.;a*=.5;}return t;}

void main(){
  vec2 uv=(FC-.5*R)/R.y;
  uv.x+=.25;
  uv*=vec2(2,1);

  float n=fbm(uv*.28-vec2(T*.01,0));
  n=noise(uv*3.+n*2.);

  float r=fbm(uv+vec2(0,T*.015)+n);
  float g=fbm(uv*1.003+vec2(0,T*.015)+n+.003);
  float b=fbm(uv*1.006+vec2(0,T*.015)+n+.006);

  // Blue/cyan base: deep blue to bright cyan
  vec3 col1=vec3(0.05,0.25,0.65);  // deep blue
  vec3 col2=vec3(0.1,0.75,0.9);    // cyan
  vec3 col3=vec3(0.85,0.45,0.65);  // pink accent
  vec3 col4=vec3(0.9,0.85,0.3);    // yellow accent

  float lum=dot(vec3(1.-r,1.-g,1.-b),vec3(.21,.71,.07));

  // Multi-color gradient based on noise values
  vec3 col=mix(col1,col2,smoothstep(0.2,0.7,lum));
  col=mix(col,col3,smoothstep(0.55,0.85,r)*0.4);
  col=mix(col,col4,smoothstep(0.6,0.9,g)*0.25);
  col=mix(col,vec3(0.95),smoothstep(0.75,0.95,lum)*0.6);

  col=mix(vec3(0.02,0.08,0.2),col,min(time*.1,1.));
  col=clamp(col,0.02,1.);
  O=vec4(col,1);
}`;

function createRenderer(canvas) {
  const gl = canvas.getContext('webgl2');
  if (!gl) return null;

  const vs = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vs, vertexSrc);
  gl.compileShader(vs);

  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fs, fragmentSrc);
  gl.compileShader(fs);
  if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
    console.error('Fragment shader error:', gl.getShaderInfoLog(fs));
    return null;
  }

  const program = gl.createProgram();
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);

  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,1,-1,-1,1,1,1,-1]), gl.STATIC_DRAW);

  const pos = gl.getAttribLocation(program, 'position');
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

  const uRes = gl.getUniformLocation(program, 'resolution');
  const uTime = gl.getUniformLocation(program, 'time');

  return {
    gl, program, buffer, vs, fs, uRes, uTime,
    updateScale() {
      const dpr = Math.max(1, window.devicePixelRatio * 0.5); // Half DPR for perf
      const rect = canvas.parentElement?.getBoundingClientRect() || { width: window.innerWidth, height: window.innerHeight };
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    },
    render(now = 0) {
      gl.clearColor(0, 0, 0, 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, now * 1e-3);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    },
    destroy() {
      gl.detachShader(program, vs);
      gl.detachShader(program, fs);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      gl.deleteProgram(program);
    },
  };
}

function onResize() {
  renderer?.updateScale();
}

function loop(now) {
  renderer?.render(now);
  raf = requestAnimationFrame(loop);
}

onMounted(() => {
  if (!canvasRef.value) return;
  renderer = createRenderer(canvasRef.value);
  if (!renderer) return;
  renderer.updateScale();
  window.addEventListener('resize', onResize);
  raf = requestAnimationFrame(loop);
});

onBeforeUnmount(() => {
  if (raf) cancelAnimationFrame(raf);
  window.removeEventListener('resize', onResize);
  renderer?.destroy();
  renderer = null;
});
</script>
