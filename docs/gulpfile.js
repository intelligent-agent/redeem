var gulp = require('gulp');
var shell = require('gulp-shell');
var less = require('gulp-less');
var rename = require("gulp-rename");
var plumber = require('gulp-plumber');



gulp.task('sphinx_to_html', shell.task('make html'));

gulp.task('less_to_css', function () {
  return gulp.src('./theme/**/styles.less')
      .pipe(plumber())
      .pipe(less())
      .pipe(rename({
          dirname: "",
          extname: ".css"
      }))
    .pipe(gulp.dest('./theme/assets/css'));
});

gulp.task('build_and_watch', ['less_to_css', 'sphinx_to_html'],function() {
   gulp.watch([
       './**/*.rst',
       './theme/*.html',
       './theme/**/*.less',
       './theme/**/*.js'
   ], ['less_to_css','sphinx_to_html']);
});

gulp.task('default', [ 'build_and_watch' ]);
